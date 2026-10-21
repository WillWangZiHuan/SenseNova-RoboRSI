# 部署三套 LIBERO 评测

[English](libero-three-reproduction.md) · [评测契约](libero-three-benchmarks.zh-CN.md)

使用 Linux x86_64、Docker、NVIDIA GPU/驱动和 NVIDIA Container Toolkit 进行 EGL
渲染。源码构建与宿主 Runner 使用 Python 3.11。为原生镜像、Agent 环境、构建目录与
结果预留存储空间。模型通过兼容 OpenAI Responses 的 endpoint 调用。

将 `RUN_ROOT` 设为绝对输出路径，`MODEL_API_KEY_FILE` 设为已有的私有 key 文件；
通过 `OPENAI_BASE_URL` 导出模型 endpoint。每个单 case 输出目录必须尚不存在。

## 运行公开 combined 镜像

以下不可变的 `v1.0.1-egl` 产物由
[上游 PR 93](https://github.com/SenseTime-FVG/RoboRSI/pull/93)基于 commit
`5b8c7f7aa6e1b67119ef3e887625601387ce917e` 发布，保留该版本内置的预设与模型路由。
镜像内容与本次迁移的当前源码独立。使用兼容其内置预设的 endpoint，或按下文重建以选择
模型。Combined CLI 接收 endpoint 与 key 文件；模型 ID 由安装后的 bundle 决定。

```bash
export LONGPP_COMBINED_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-long-plus-plus@sha256:814139261e914b114cb89a359c6a39d4f409a556f79928e986b6ade3dfe7dc7a'
export ULTRA_COMBINED_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-ultra-long@sha256:814139261e914b114cb89a359c6a39d4f409a556f79928e986b6ade3dfe7dc7a'
export PRO_COMBINED_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-pro@sha256:a83417f1459a4c555c457caa82ef00a5de50191e3d8deb943894fa9285cff172'
docker pull "$LONGPP_COMBINED_IMAGE"
docker pull "$ULTRA_COMBINED_IMAGE"
docker pull "$PRO_COMBINED_IMAGE"
```

Long++ 与 Ultra-Long 使用不同 GHCR package 名称，但 LiLo 镜像内容相同。每个镜像
包含对应 Benchmark、三套 Agent bundle、sealed ICL package 和 tokenizer。
模型凭据在运行时提供。

运行一个 Long++ case：

```bash
mkdir -p "$RUN_ROOT/results"
docker run --rm --gpus all \
  --mount "type=bind,src=$MODEL_API_KEY_FILE,dst=/run/secrets/model_api.key,readonly" \
  --mount "type=bind,src=$RUN_ROOT/results,dst=/results" \
  "$LONGPP_COMBINED_IMAGE" \
  --benchmark libero_long_plus_plus --task t00-i01 \
  --run-id longpp-one --results-root /results/longpp-one \
  --api-key-file /run/secrets/model_api.key --base-url "$OPENAI_BASE_URL"
```

Ultra-Long 使用 `$ULTRA_COMBINED_IMAGE`、`--benchmark libero_ultra_long` 和
`--task t00-i01`；PRO 使用 `$PRO_COMBINED_IMAGE`、`--benchmark libero_pro` 和
`--task libero_spatial_task-t00-i03`。

通过 subset runner 运行固定子集：

```bash
docker run --rm --gpus all --entrypoint python \
  --mount "type=bind,src=$MODEL_API_KEY_FILE,dst=/run/secrets/model_api.key,readonly" \
  --mount "type=bind,src=$RUN_ROOT/results,dst=/results" \
  "$LONGPP_COMBINED_IMAGE" \
  -B /opt/roborsi/scripts/libero_three/run_combined_subset.py \
  --benchmark libero_long_plus_plus --run-id longpp-subset \
  --results-root /results/longpp-subset --max-concurrent 16 --gpu-count 1 \
  --api-key-file /run/secrets/model_api.key --base-url "$OPENAI_BASE_URL"
```

Ultra-Long 与 PRO 使用对应镜像和 benchmark；context map 分别规划 12、9、80 个
case。重复 `--task` 可选择较少 case。默认并发为 16，共用一张 GPU，请按宿主容量配置。
Runner 保留每次尝试；只有镜像/源码、Agent、ICL、endpoint、超时指纹均一致，进程
退出码为零、case 身份一致且原生 score 摘要完整时，才复用结果。只要仍有 case 缺少
已验证的原生终态，就以非零状态退出。其服务采用固定子集与 1× 边界。

Combined 模式让 Agent 与 Benchmark 共用容器；下文的独立容器模式为每个 case
提供独立的 Agent 文件系统和网络。

## 使用公开输入重建 Agent

在当前 checkout 根目录执行。将 `LIBERO_BUILD_ROOT` 设为源码目录外的路径；其中
`extracted-assets`、bundle 与 build 子目录必须尚不存在，并为本次构建使用新的
`dist/agent/`。将 `AGENT_IMAGE_TAG`、`LILO_IMAGE_TAG`、`PRO_IMAGE_TAG` 设为你的
容器仓库中的新 tag，发布前完成登录。

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[runtime]' build uv tokenizers==0.22.2
mkdir -p "$LIBERO_BUILD_ROOT"
```

拉取上面的 Long++ combined 镜像后，从未启动的容器中复制资产；此操作不会运行
模拟器或 Agent。按当前资产锁验证并暂存三个 package family 与 tokenizer：

```bash
ASSET_CONTAINER=$(docker create "$LONGPP_COMBINED_IMAGE")
docker cp "$ASSET_CONTAINER:/opt/roborsi-agent-assets" "$LIBERO_BUILD_ROOT/extracted-assets"
docker rm "$ASSET_CONTAINER"
python scripts/libero_three/prepare_agent_assets.py \
  --longpp-root "$LIBERO_BUILD_ROOT/extracted-assets/longpp/packages" \
  --ultra-root "$LIBERO_BUILD_ROOT/extracted-assets/ultra/packages" \
  --pro-root "$LIBERO_BUILD_ROOT/extracted-assets/pro/packages" \
  --tokenizer "$LIBERO_BUILD_ROOT/extracted-assets/tokenizer.json" \
  --output dist/agent/libero-three-assets
```

清单包含 12 个 Long++ package、9 个 Ultra-Long package，以及供 80 个 case 使用
的 40 个 PRO package；准备程序拒绝内容变化或额外 package。如果已有原始冻结 family
目录格式的 package，可先运行
`prepare_context.py --benchmark NAME --source FAMILY --destination NEW_DIRECTORY`
复制并校验，再把输出的 `packages/` 目录传给 `prepare_agent_assets.py`。

为三个 bundle 配置镜像内 tokenizer 路径和哈希。若 endpoint 使用其他模型 ID，
将三处 `gpt-6-astra` 一致替换：

```bash
python -m roborsi.agents.package \
  --config configs/agents/libero_three/long_plus_plus_v13.yaml \
  --name libero_long_plus_plus_v13 \
  --set 'runtime.llm.model="gpt-6-astra"' \
  --set 'runtime.context.tokenizer_file="/opt/roborsi-agent-assets/tokenizer.json"' \
  --set 'runtime.context.tokenizer_sha256="0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3"' \
  --output "$LIBERO_BUILD_ROOT/bundle-longpp"
python -m roborsi.agents.package \
  --config configs/agents/libero_three/ultra_long_v13.yaml \
  --name libero_ultra_long_v13 \
  --set 'runtime.llm.model="gpt-6-astra"' \
  --set 'runtime.context.tokenizer_file="/opt/roborsi-agent-assets/tokenizer.json"' \
  --set 'runtime.context.tokenizer_sha256="0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3"' \
  --output "$LIBERO_BUILD_ROOT/bundle-ultra"
python -m roborsi.agents.package \
  --config configs/agents/libero_three/pro.yaml --name libero_pro \
  --set 'runtime.llm.model="gpt-6-astra"' \
  --set 'runtime.context.tokenizer_file="/opt/roborsi-agent-assets/tokenizer.json"' \
  --set 'runtime.context.tokenizer_sha256="0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3"' \
  --output "$LIBERO_BUILD_ROOT/bundle-pro"
python -m build --wheel --outdir dist/agent "$LIBERO_BUILD_ROOT/bundle-longpp"
python -m build --wheel --outdir dist/agent "$LIBERO_BUILD_ROOT/bundle-ultra"
python -m build --wheel --outdir dist/agent "$LIBERO_BUILD_ROOT/bundle-pro"
```

合并三个 wheel 的 requirements 与 Agent 基础 requirements。预设声明
`tokenizers==0.22.2`；另外加入 SciPy，因为 combined 镜像会检查
`scipy.spatial.transform.Rotation`。版本 1.15.3 与原生 base 对齐，生成的 lock
固定全部版本与哈希。
本地框架 wheel 提供当前 checkout 的依赖元数据，Dockerfile 安装同一 checkout 的源码。

```bash
python -m build --wheel --outdir "$LIBERO_BUILD_ROOT/framework-wheel" .
python -c 'from pathlib import Path; import sys; print("roborsi @ " + next(Path(sys.argv[1]).glob("roborsi-*.whl")).resolve().as_uri())' \
  "$LIBERO_BUILD_ROOT/framework-wheel" > "$LIBERO_BUILD_ROOT/roborsi-override.txt"
printf 'scipy==1.15.3\n' > "$LIBERO_BUILD_ROOT/combined-runtime.in"
uv pip compile \
  "$LIBERO_BUILD_ROOT/bundle-longpp/requirements.in" \
  "$LIBERO_BUILD_ROOT/bundle-ultra/requirements.in" \
  "$LIBERO_BUILD_ROOT/bundle-pro/requirements.in" \
  agents/python/requirements.in "$LIBERO_BUILD_ROOT/combined-runtime.in" \
  --overrides "$LIBERO_BUILD_ROOT/roborsi-override.txt" --no-emit-package roborsi \
  --python-version 3.11 --generate-hashes --output-file dist/agent/requirements.txt
docker build --target libero_three -f agents/python/Dockerfile \
  --build-arg AGENT_REQUIREMENTS=dist/agent/requirements.txt \
  --build-arg 'AGENT_WHEEL=dist/agent/roborsi_agent_bundle_libero_*.whl' \
  --build-arg LIBERO_THREE_ASSETS=dist/agent/libero-three-assets \
  -t "$AGENT_IMAGE_TAG" .
docker push "$AGENT_IMAGE_TAG"
export AGENT_IMAGE=$(docker image inspect "$AGENT_IMAGE_TAG" --format '{{index .RepoDigests 0}}')
```

镜像构建会验证 bundle 任务 map、全部 package 哈希、清单与 tokenizer 身份，并执行
依赖检查。保留生成的 lock、bundle manifest、源码 revision 和实际 repository digest。

## 重建并注册 Benchmark

按照 [PRO 指南](../benchmarks/libero_pro/README.md)准备完整评测目录，并将
`PRO_EVALUATION_SOURCE` 设为该目录。要求 SHA-256 为
`04ae2020acf89315108a68743f99f8fe9c4cb9fc47e67712298a25a7179d616a`。
固定原生源码与资产细节见 [LiLo 说明](../benchmarks/libero_lilo/README.md)。
构建并发布当前两个 context：

```bash
python -m benchmarks.package --benchmark libero_lilo --output "$LIBERO_BUILD_ROOT/build-lilo"
python -m benchmarks.package --benchmark libero_pro --output "$LIBERO_BUILD_ROOT/build-pro"
python -m benchmarks.libero_pro.assets \
  --source "$PRO_EVALUATION_SOURCE" --output-dir "$LIBERO_BUILD_ROOT/pro-assets" \
  --build-context "$LIBERO_BUILD_ROOT/build-pro"
docker build -t "$LILO_IMAGE_TAG" "$LIBERO_BUILD_ROOT/build-lilo"
docker build -t "$PRO_IMAGE_TAG" "$LIBERO_BUILD_ROOT/build-pro"
docker push "$LILO_IMAGE_TAG"
docker push "$PRO_IMAGE_TAG"
export LILO_IMAGE=$(docker image inspect "$LILO_IMAGE_TAG" --format '{{index .RepoDigests 0}}')
export PRO_IMAGE=$(docker image inspect "$PRO_IMAGE_TAG" --format '{{index .RepoDigests 0}}')
```

在同一批镜像中生成 manifest，使代码、内置资产与运行时标识一致。以下选择固定的
12/9/80 子集：

```bash
mkdir -p "$RUN_ROOT/registry/libero_long_plus_plus" \
  "$RUN_ROOT/registry/libero_ultra_long" "$RUN_ROOT/registry/libero_pro"
docker run --rm --entrypoint python \
  --mount "type=bind,src=$RUN_ROOT/registry,dst=/output" "$LILO_IMAGE" \
  -m benchmarks.libero_lilo.manifest --image "$LILO_IMAGE" \
  --benchmark libero_long_plus_plus --profile migration_subset \
  --output /output/libero_long_plus_plus/manifest.json
docker run --rm --entrypoint python \
  --mount "type=bind,src=$RUN_ROOT/registry,dst=/output" "$LILO_IMAGE" \
  -m benchmarks.libero_lilo.manifest --image "$LILO_IMAGE" \
  --benchmark libero_ultra_long --profile migration_subset \
  --output /output/libero_ultra_long/manifest.json
docker run --rm --entrypoint python \
  --mount "type=bind,src=$RUN_ROOT/registry,dst=/output" "$PRO_IMAGE" \
  -m benchmarks.libero_pro.manifest --image "$PRO_IMAGE" --profile migration_subset \
  --output /output/libero_pro/manifest.json
```

Manifest 为 EGL 申请一张 GPU。`official` 选择 benchmark 全集；所提供的专用
context map 覆盖固定子集。`--plus9-on-failure` 用于单独记录的继续执行条件。

## 使用独立容器评测

使用重建后的 Agent digest 与已安装 bundle，凭据只传入 Agent。先查看展开后的
Long++ 计划：

```bash
export OPENAI_API_KEY="$(cat "$MODEL_API_KEY_FILE")"
bench eval --registry-root "$RUN_ROOT/registry" \
  --results-root "$RUN_ROOT/results" --run-id longpp-plan \
  --benchmark libero_long_plus_plus --seed 0 \
  --agent-image "$AGENT_IMAGE" --agent-config bundle:libero_long_plus_plus_v13 \
  --agent-credential-env OPENAI_API_KEY --agent-credential-env OPENAI_BASE_URL \
  --agent-set 'runtime.llm.model="gpt-6-astra"' \
  --max-concurrent 1 --timeout-s 43200 --case-timeout-s 14400 --dry-run
```

去掉 `--dry-run`，选择新 run ID 并保持所选模型 ID，即可执行。添加
`--task libero_long_plus_plus:t00-i01` 可只跑一个 case。其他子集使用以下组合：

| Benchmark | Bundle | 示例任务 |
| --- | --- | --- |
| `libero_ultra_long` | `bundle:libero_ultra_long_v13` | `libero_ultra_long:t00-i01` |
| `libero_pro` | `bundle:libero_pro` | `libero_pro:libero_spatial_task-t00-i03` |

使用 `--resume-from OLD_RUN_ID` 时选择新 run ID 并保持锁定输入一致。
结果查看见[评测指南](evaluation.zh-CN.md)。分别统计有分数终态、Agent/基础设施失败
以及原生证据。

## 组合重建后的镜像

将 `NEW_LILO_COMBINED_TAG` 和 `NEW_PRO_COMBINED_TAG` 设为新 tag。在仓库根目录，
使用前面取得的实际 Agent 与 Benchmark digest 构建：

```bash
docker build -f benchmarks/libero_three_combined/Dockerfile \
  --build-arg AGENT_IMAGE="$AGENT_IMAGE" --build-arg BENCHMARK_IMAGE="$LILO_IMAGE" \
  --build-arg ROBORSI_REVISION="$(git rev-parse HEAD)" \
  -t "$NEW_LILO_COMBINED_TAG" .
docker build -f benchmarks/libero_three_combined/Dockerfile \
  --build-arg AGENT_IMAGE="$AGENT_IMAGE" --build-arg BENCHMARK_IMAGE="$PRO_IMAGE" \
  --build-arg ROBORSI_REVISION="$(git rev-parse HEAD)" \
  -t "$NEW_PRO_COMBINED_TAG" .
docker push "$NEW_LILO_COMBINED_TAG"
docker push "$NEW_PRO_COMBINED_TAG"
docker image inspect "$NEW_LILO_COMBINED_TAG" "$NEW_PRO_COMBINED_TAG" \
  --format '{{json .RepoDigests}}'
```

在 combined 命令中使用新的 repository digest。Long++ 与 Ultra-Long 共用重建后的
LiLo combined 镜像。将新的源码/镜像标识记录在本次运行中；
[PR 93 历史验证](libero-three-subset-validation.zh-CN.md)描述原始产物，不表示已重跑
当前构建。
