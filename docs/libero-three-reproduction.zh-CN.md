# 复现三套 LIBERO 评测

下方固定镜像属于历史交付，复现时需使用匹配的源码版本。当前 RoboRSI 要求重建镜像、
更新工厂并使用 `/roborsi/` 挂载；新运行请遵循
[迁移指南](source-zh/rst_source/usage/roborsi_migration.rst)。

本文说明如何在一台干净的 Linux 机器上运行已交付的 LIBERO-PRO、Long++
和 Ultra-Long 评测。原先从 m 集群读取的运行资产都已经封装进镜像：Benchmark
镜像包含模拟器、BDDL 和初始状态；共享 Agent 镜像包含三套 ICL 包、锁定的
tokenizer 和已安装 Agent bundle。镜像不包含模型权重和凭证。

## 准备条件

- Linux `x86_64`、Docker、Python 3.11；镜像解压后约占 10.4 GB，另需预留
  结果空间。
- 能访问 `registry.example.com/roborsi/ms-ccr`。
- 一个提供 `gpt-6-astra` 的 OpenAI Responses 兼容端点及 API key。
- 本仓库 PR 对应版本的 checkout。不需要 AFS 或 m 集群挂载。

本评测条件不运行本地 VLA 或 SAM3 模型，因此 GPU 不是模型依赖。交付的
manifest 默认申请一张 GPU，以提高 MuJoCo EGL 渲染速度和一致性；CPU 软件
渲染也能运行，但明显更慢，只建议用于小规模验证。

## 锁定镜像

```bash
export AGENT_IMAGE='registry.example.com/roborsi/ms-ccr/heart-libero-three-agent@sha256:33e4f5bd9947a208e83cbbbdc6b70297b0ebeb16893839ac2fb42fc627a1253e'
export LILO_IMAGE='registry.example.com/roborsi/ms-ccr/heart-libero-lilo@sha256:4e795cf962ff4680f88a757d4edba901440374e0c797246fc960221ba7822f81'
export PRO_IMAGE='registry.example.com/roborsi/ms-ccr/heart-libero-pro@sha256:5fbf5694f17bd9500c1b495461e881464ecc29ebc26687d067b3c9a9a69606cf'

docker pull "$AGENT_IMAGE"
docker pull "$LILO_IMAGE"
docker pull "$PRO_IMAGE"
```

## 单镜像部署

只能为每个作业指定一个镜像的调度平台，可使用
[`benchmarks/libero_three_combined/`](../benchmarks/libero_three_combined/README.md)
中的合成配方。已发布的不可变镜像为：

```bash
export LONGPP_COMBINED_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-long-plus-plus@sha256:814139261e914b114cb89a359c6a39d4f409a556f79928e986b6ade3dfe7dc7a'
export ULTRA_COMBINED_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-ultra-long@sha256:814139261e914b114cb89a359c6a39d4f409a556f79928e986b6ade3dfe7dc7a'
export PRO_COMBINED_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-pro@sha256:a83417f1459a4c555c457caa82ef00a5de50191e3d8deb943894fa9285cff172'
```

Long++ 和 Ultra-Long 按规范使用独立 GHCR Package，但二者有意复用完全相同的
LiLo+Agent 镜像内容；PRO 使用 PRO+Agent 镜像。镜像内包含 Benchmark、Agent bundle、ICL 和 tokenizer；运行时只需
模型 endpoint、只读 API key 文件和可写结果目录。由于凭证和 Benchmark 同容器，该模式
隔离性弱于标准双容器部署。

覆盖 entrypoint 即可执行固定子集：

```bash
docker run --rm --gpus all \
  --entrypoint python \
  -v /path/to/model_api.key:/run/secrets/model_api.key:ro \
  -v "$RUN_ROOT/results:/results" "$LONGPP_COMBINED_IMAGE" \
  -B /opt/roborsi/scripts/libero_three/run_combined_subset.py \
  --benchmark libero_long_plus_plus --run-id longpp-subset \
  --results-root /results/longpp-subset --max-concurrent 16 --gpu-count 1 \
  --api-key-file /run/secrets/model_api.key \
  --base-url https://your-responses-endpoint.example/v1
```

Long++ 和 Ultra-Long 共用 `LILO_IMAGE`，由 manifest 选择服务；PRO 使用
`PRO_IMAGE`。三者共用 `AGENT_IMAGE`，每次评测选择其中一个已安装 bundle。

## 安装 Runner

在仓库根目录执行：

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

可以使用机器已配置的内部 pip 源；这不会改变容器内的锁定依赖。

## 生成本地 Benchmark registry

manifest 由对应的 Benchmark 镜像直接生成，保证运行时身份、任务列表和镜像
digest 一致。

```bash
export RUN_ROOT="$PWD/../work/libero-three-reproduction"
mkdir -p "$RUN_ROOT/registry/libero_long_plus_plus" \
  "$RUN_ROOT/registry/libero_ultra_long" \
  "$RUN_ROOT/registry/libero_pro" \
  "$RUN_ROOT/results"

docker run --rm --entrypoint python \
  -v "$RUN_ROOT/registry:/output" "$LILO_IMAGE" \
  -m benchmarks.libero_lilo.manifest \
  --image "$LILO_IMAGE" --benchmark libero_long_plus_plus \
  --profile migration_subset \
  --output /output/libero_long_plus_plus/manifest.json

docker run --rm --entrypoint python \
  -v "$RUN_ROOT/registry:/output" "$LILO_IMAGE" \
  -m benchmarks.libero_lilo.manifest \
  --image "$LILO_IMAGE" --benchmark libero_ultra_long \
  --profile migration_subset \
  --output /output/libero_ultra_long/manifest.json

docker run --rm --entrypoint python \
  -v "$RUN_ROOT/registry:/output" "$PRO_IMAGE" \
  -m benchmarks.libero_pro.manifest \
  --image "$PRO_IMAGE" --profile migration_subset \
  --output /output/libero_pro/manifest.json
```

预期任务数分别为 Long++ 12、Ultra-Long 9、PRO 80。在调用模型前先验证完整
执行计划：

```bash
export OPENAI_API_KEY='replace-me'
export OPENAI_BASE_URL='https://your-responses-endpoint.example/v1'

python scripts/libero_three/run.py \
  --benchmark libero_long_plus_plus \
  --registry-root "$RUN_ROOT/registry" \
  --agent-config bundle:libero_long_plus_plus_v13 \
  --agent-image "$AGENT_IMAGE" \
  --agent-credential-env OPENAI_API_KEY \
  --agent-credential-env OPENAI_BASE_URL \
  --results-root "$RUN_ROOT/results" --run-id longpp-plan --dry-run

python scripts/libero_three/run.py \
  --benchmark libero_ultra_long \
  --registry-root "$RUN_ROOT/registry" \
  --agent-config bundle:libero_ultra_long_v13 \
  --agent-image "$AGENT_IMAGE" \
  --agent-credential-env OPENAI_API_KEY \
  --agent-credential-env OPENAI_BASE_URL \
  --results-root "$RUN_ROOT/results" --run-id ultra-plan --dry-run

python scripts/libero_three/run.py \
  --benchmark libero_pro \
  --registry-root "$RUN_ROOT/registry" \
  --agent-config bundle:libero_pro \
  --agent-image "$AGENT_IMAGE" \
  --agent-credential-env OPENAI_API_KEY \
  --agent-credential-env OPENAI_BASE_URL \
  --results-root "$RUN_ROOT/results" --run-id pro-plan --dry-run
```

key 和 endpoint 只会传给隔离的 Agent 容器，不会传给 Benchmark 容器，也不会
写入命令参数、manifest 或结果记录。

## 运行真实模型小样本

先运行一个代表性 case。下面是实际 Agent 评测，不是固定动作或 no-op 模拟器
检查。

```bash
bench eval \
  --registry-root "$RUN_ROOT/registry" \
  --results-root "$RUN_ROOT/results" --run-id longpp-one-case \
  --agent-config bundle:libero_long_plus_plus_v13 \
  --agent-image "$AGENT_IMAGE" \
  --agent-credential-env OPENAI_API_KEY \
  --agent-credential-env OPENAI_BASE_URL \
  --benchmark libero_long_plus_plus \
  --task libero_long_plus_plus:t00-i01 --seed 0 \
  --max-concurrent 1 --case-timeout-s 86400
```

Ultra-Long 使用 bundle `libero_ultra_long_v13`、benchmark
`libero_ultra_long` 和 task `libero_ultra_long:t00-i01`。PRO 使用 bundle
`libero_pro`、benchmark `libero_pro` 和 task
`libero_pro:libero_spatial_task-t00-i03`。

## 运行三个迁移子集

去掉上述三条计划命令中的 `--dry-run`，使用新的 run ID，并按可用模拟器容量
设置并发。例如：

```bash
python scripts/libero_three/run.py \
  --benchmark libero_long_plus_plus \
  --registry-root "$RUN_ROOT/registry" \
  --agent-config bundle:libero_long_plus_plus_v13 \
  --agent-image "$AGENT_IMAGE" \
  --agent-credential-env OPENAI_API_KEY \
  --agent-credential-env OPENAI_BASE_URL \
  --results-root "$RUN_ROOT/results" --run-id longpp-full \
  --max-concurrent 1 --case-timeout-s 86400
```

再按上面的 benchmark/bundle 对运行 Ultra-Long 和 PRO。主 1x 分数不要启用
`plus9_on_failure`。只有在锁定输入完全不变时，才可用新的 run ID 配合
`--resume-from OLD_RUN_ID`。

## 验证输出

每个完成的 case 都应包含 `result.json`、`native/score.json`、有图像时生成的
原生视频、`runner_trace/`、media 和完整 Agent trace。只有 `success` 和原生
`task_failure` 是有效评测终态；基础设施错误或 Agent 错误都不是分数。计划
case 数应为 12、9 和 80。

已记录的真实模型证据及其严格限制见
[`libero-three-benchmarks.zh-CN.md`](libero-three-benchmarks.zh-CN.md)。特别是
PRO 的 786/800 是条件对齐的完整集参考结果，不是本仓库 fixed-state-3 的
80-case 子集新跑成绩。
