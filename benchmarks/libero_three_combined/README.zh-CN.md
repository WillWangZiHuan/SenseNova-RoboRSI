# 三套 LIBERO combined 部署

[English](README.md) · [完整部署指南](../../docs/libero-three-reproduction.zh-CN.md)

该镜像将已验证的三套 LIBERO Agent 镜像与 LiLo 或 PRO Benchmark 镜像组合。
Long++ 与 Ultra-Long 共用 LiLo 组合，支持每个任务只能指定一个镜像的调度器。
镜像内部的 Agent 与原生 Python 包目录分别存放。

## 公开镜像

以下不可变 GHCR 产物由上游 PR 93 基于 commit
`5b8c7f7aa6e1b67119ef3e887625601387ce917e` 发布，保留原有内置预设。重建当前源码、
选择 endpoint 支持的模型 ID，见完整部署指南。

```bash
export LONGPP_COMBINED_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-long-plus-plus@sha256:814139261e914b114cb89a359c6a39d4f409a556f79928e986b6ade3dfe7dc7a'
export ULTRA_COMBINED_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-ultra-long@sha256:814139261e914b114cb89a359c6a39d4f409a556f79928e986b6ade3dfe7dc7a'
export PRO_COMBINED_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-pro@sha256:a83417f1459a4c555c457caa82ef00a5de50191e3d8deb943894fa9285cff172'
docker pull "$LONGPP_COMBINED_IMAGE"
docker pull "$ULTRA_COMBINED_IMAGE"
docker pull "$PRO_COMBINED_IMAGE"
```

## 运行一个 case

将 `RUN_ROOT`、`MODEL_API_KEY_FILE`、`OPENAI_BASE_URL` 分别设为输出根目录、私有
key 文件和模型 endpoint。每个单 case 输出目录必须尚不存在。

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

默认 entrypoint 是 `run_combined.py`。运行 12/9/80 子集时，用
`--entrypoint python`，并在镜像引用后传入
`-B /opt/roborsi/scripts/libero_three/run_combined_subset.py`。
完整命令和经过身份验证的结果复用规则见[部署指南](../../docs/libero-three-reproduction.zh-CN.md)。

## 重建

按照[公开输入重建步骤](../../docs/libero-three-reproduction.zh-CN.md)构建三套已安装
Agent bundle 与原生 Benchmark 镜像。将 `AGENT_IMAGE`、`LILO_IMAGE`、`PRO_IMAGE`
设为实际 repository digest，并选择新的 combined tag。在仓库根目录执行：

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

模型凭据在运行时传入。Combined 模式让 Agent 与 Benchmark 共用容器；需要每个 case
拥有独立 Agent 文件系统时，通过 `bench eval` 运行独立镜像。保留源码 revision、
两个输入 digest 与新的输出 digest。

[上游验证](../../docs/libero-three-subset-validation.zh-CN.md)记录 PR 93 的历史真实
模型运行。本次迁移未重新构建或执行这些 GPU/模型实验。
