# LIBERO-PRO、Long++ 与 Ultra-Long 接入说明

本文说明三套 benchmark 的冻结评测约束、外部依赖、AFS 目录布局和源码运行方式。
英文版见 [libero-three-benchmarks.md](libero-three-benchmarks.md)。

## 评测契约

| Benchmark | 全量集合 | 本次迁移子集 | 官方 1× 预算 | 主指标 |
| --- | ---: | ---: | ---: | --- |
| LIBERO-PRO Task/Swap | 8 suites × 10 tasks × 10 states = 800 | 固定 state 3 的 80 个任务 | 10,000 物理步 | 最终目标成功 |
| LIBERO-Long++ | 12 配置 × 10 次裸 reset = 120 | 固定 state 1 的 12 个配置 | 每个顺序技能 200 步 | 顺序前缀比例；全部完成才成功 |
| LIBERO-Ultra-Long | 9 配置 × 10 次裸 reset = 90 | 固定 state 1 的 9 个配置 | 每个顺序技能 200 步 | 顺序前缀比例；全部完成才成功 |

`plus9_on_failure` 默认关闭。开启后，只有在官方 1× 边界失败的案例才能在同一环境、
同一 Agent 对话内继续，累计最多 10×。正式 `result.json` 和聚合分数始终使用不可变的
1× 快照；`native/score.json` 额外记录恢复过程和真实物理步数。

Long++/Ultra-Long 的重复编号不是随机种子。官方 profile 做十次发布版裸随机 reset；
迁移 profile 明确固定为 state 1。评分器只接受发布版技能顺序的连续前缀，不用普通
LIBERO 最终目标成功替代顺序成功。

两套长序列 benchmark 使用历史冻结的
`lilo-instance-pose-feedback-v1` 观测协议。观测包含注册实例名、实时世界坐标、碰撞几何
上下界、夹爪接触、持有物体以及当前技能进度。该通道只读，不推进评分器；结果不能和
旧的纯视觉条件混为同一评测条件。

迁移接口还保留 `libero-robot-state-feedback-v1`：它将旧 v13 直接工具返回的
`robot0_eef_pos`、xyzw 四元数和 `robot0_gripper_qpos` 以具名字段随每次观测返回，同时
继续保留策略所需的 8 维 `states`。`heart_action` 的 action schema 对每个旧 direct-control
primitive 明确标注语义；特别是 `rotate_wrist` 表示保持末端位置的原地腕部旋转，不能用
`move_pose.target_yaw` 替代。该兼容层只恢复旧工具契约，不改变任务、评分器、初始化或
物理步数预算。

历史报告中的版本对应关系需要特别区分：Long++ 和 Ultra-Long 子集使用 v13 的
no-tool、token-accurate 条件；PRO v21 全量 800 例是在十个初态上展开 v18 persistent
memory 策略，其可比的 80 例代表子集是固定 state 2 的 v18。当前仓库提供的 PRO
preset/package 复现的是后续 v19 safe-carry、固定 state 3，因此当前 PRO 数字不能直接
作为 v21 的子集对照。

## 交付状态与实测证据

以下均使用真实模型和模拟器，并遵守官方 1× 步数边界，没有启用
`plus9_on_failure`。Long++ 和 PRO 的“诊断聚合”包含后续同条件严格 1× 重试，不能写成
单次完整 pass；Ultra-Long 是一轮同配置并行分片的干净完整 pass。

| Benchmark / 条件 | 实际例数 | success | 平均原生分数 | 内部证据（相对 `../work/libero_three/`） |
| --- | ---: | ---: | ---: | --- |
| Long++ v13，state 1，首轮 | 12 × 1 | 9/12 | 0.9375 | `source-repro-v3/libero_long_plus_plus/summary.json` |
| Long++ v13，诊断聚合 | 12 × 1 | 12/12 | 1.0000 | `source-longpp-best-valid-v1/summary.json` |
| Ultra-Long v13，state 1，干净 pass | 9 × 1 | 8/9 | 0.9583 | `source-v13-compat-geom-full-r3/summary.json` |
| PRO v19，state 3，首轮 | 80 × 1 | 72/80 | 0.9000 | `source-pro-combined-v1/summary.json` |
| PRO v19，诊断聚合 | 80 × 1 | 76/80 | 0.9500 | `source-pro-best-valid-v1/summary.json` |

冻结的内部对照为 Long++ v13 12/12、Ultra-Long v13 8/9、PRO v19 state-3
75/80。PRO v21 的 756/800 属于 v18 persistent-memory 策略延续，代表子集是 state 2，
与本交付的 v19/state-3 条件不同。上游 [LiLo-VLA](https://github.com/YY-GX/LiLo-VLA)、
[LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO) 和
[LIBERO-PRO](https://github.com/RLinf/LIBERO-PRO) 没有公开与这三个固定迁移子集、Agent
和预算完全相同的成绩，因此不补猜其他方法数值，也不做跨条件排名。

代表性成功/失败案例的完整目录分别是：Long++ `source-repro-v3/libero_long_plus_plus/cases/`
下的 `t00-i01` / `t02-i01`，Ultra-Long `source-v13-compat-geom-full-r3/cases/` 下的
`t00-i01` / `t01-i01`，PRO `source-pro-combined-v1/cases/` 下的
`libero_10_swap-t00-i03` / `libero_10_swap-t06-i03`。每个目录保留 `result.json`、
`native/score.json`、episode 视频、Runner trace、Agent full trace 和去凭证后的配置；聚合目录
中的符号链接只用于汇总，权威文件位于链接目标。

首轮产物的时间戳跨度约为 Long++ 27 分钟、Ultra-Long 80 分钟、PRO 2.3 小时；这是
当时并发运行的实测墙钟时间，不是单卡串行保证值。相应 trace 记录了 496、969、1923
次模型请求；输入 token（包含后来从 cache 命中的部分）约为 8.0M、92.3M、41.6M，输出
token 约为 159k、231k、147k。内部 TokenHub 没有随交付提供可结算单价，无法诚实换算
货币成本；接收方应按实际 endpoint 的 input/output/cache 单价计算。

## “仓库 + 配置”运行边界

推荐布局如下：

```text
newrpent/
├── NewRPent/                 # 纯 Git 仓库
└── work/libero_three/        # 私有配置、ICL、运行环境、日志和结果
```

`work/` 不放进仓库，原因是它含机器路径、密钥位置、大资产、生成结果和可变缓存。这样可
独立更新或替换仓库而不碰运行数据，也不会把私有路径或大文件提交到 Git。

在能挂载同一 AFS 的其他机器上，运行所需信息由两部分组成：

1. `NewRPent/` 仓库；
2. 仓库外的一份 `source-runtime.afs.json` 私有主机配置。

主机配置必须完整指向以下依赖；无需再猜测隐含路径：

- Agent Python 或启动 wrapper；
- OpenAI-compatible endpoint 与只保存密钥的文件；
- Long++、Ultra-Long、PRO 三套密封 ICL package 根目录；
- LiLo-VLA、LIBERO、LIBERO-PRO 的固定源码树及各自 Python 环境；
- LIBERO assets、BDDL、init states，以及需要时才使用的 datasets；
- Pi0.5 checkpoint、SAM3 checkpoint、上下文 tokenizer，以及 OpenPI 使用的固定
  PaliGemma tokenizer/cache 根目录；
- PRO 使用的 Pi0.5/SAM3 RPC 地址，以及通用 MCP 地址字段；
- 每套 benchmark 的固定 revision 和运行环境变量。

公开模板是 `configs/libero_three/source-runtime.example.json`，逻辑资产锁是
`configs/libero_three/assets.lock.json`。真实 AFS 绝对路径和密钥文件位置只写到仓库外的
私有配置。目标机器或基础容器还需要 Ubuntu 22.04 兼容的 `python3.10` 以及 Linux
EGL/GL 运行库；Python package 依赖由配置中的解释器环境或 wrapper 提供。当前 LiLo
venv 的入口明确解析到 `/usr/bin/python3.10`，所以仅挂载 AFS 但缺少该系统解释器的主机
不能直接运行 Long++/Ultra-Long。

标准 Agent 入口位于 `configs/agents/libero_three/`。Long++ 和 Ultra-Long 通过
`v13.yaml` 继承共同的 no-tool、token-accurate 配置；PRO 使用 `pro_v19.yaml`。
`base.yaml` 和 `v13.yaml` 只用于继承，不能直接作为评测 preset。

PRO 的 `pythonpath` 必须指向固定 revision 的 LIBERO-PRO checkout 根目录，不能指向旧的
内层 `libero/` 目录；实际导入名是 `liberopro.liberopro`。assets、BDDL 和 init states
分别由主机配置指定，可以来自独立的冻结资产包。源码评测不读取 demonstration，所以全新
checkout 没有 `liberopro/datasets/` 是正常的。发布源码中的个别 pruned init 文件可能是
空集合，部分变体 BDDL 也可能无法解析，因此用于评测的 `init_states` 和 `bddl_files` 必须
指向全量评测资产；预检会实际加载并解析 80 个选定案例，任何空集合、缺失 state 或无效
BDDL 都会在分配模拟器前失败。Ubuntu 基础环境需提供 `python3.10`、`libgl1`、
`libegl1` 和 `libglib2.0-0`。

这些系统依赖同时明确列在配置的 `system_packages` 中。`openpi_data_home` 必须预先包含
`big_vision/paligemma_tokenizer.model`；预检会校验固定大小与哈希，使 Pi0.5 启动不再
依赖从 GCS 临时下载。

## 当前三套依赖策略

- Long++ 与 Ultra-Long 复现历史 v13 条件：主机配置中显式关闭 VLA 和 SAM3；使用
  LiLo 官方 Python 3.10 仿真环境。
- PRO 复现 v19 tool contract：必须提供 Pi0.5 与 SAM3。模型服务和 PRO native runner 使用
  配置指定的兼容 Python/wrapper，PRO checkout 只通过该进程的 `PYTHONPATH` 注入，避免把
  另一套 site-packages 混入并污染 Torch 版本。
- PRO 通过仓库现有 native LIBERO toolkit 暴露 `back_project`、`pi0_pick` 等历史工具；
  Long++/Ultra-Long 走独立 Benchmark HTTP 服务和 action/feedback primitive 协议。
- Agent preset 对 transient transport/5xx 使用最多三次有界重试；PRO reasoning 为 low，
  Long++/Ultra-Long 为 max，并开启 Responses prompt caching。
- Long++/Ultra-Long 还固定复现 v13 的 token-accurate 上下文策略：1,050,000 token
  窗口、128,000 输出预留、32,768 工具/协议预留、0.75 摘要触发比例、至少保留最近
  8 个完整工具往返和 2 组图像。`run_source.py` 从主机配置注入本地 tokenizer 及锁定
  SHA-256；在触发线以下完整保留文本历史，不能用固定 recent-turn 截断替代。

## 准备并校验 ICL

准备命令会校验源 package 的每个文件，将其复制到外部 `work/`，再校验副本并生成诊断用
`package-map.json`。权威 task-to-package map 始终保存在仓库配置中。

```bash
python scripts/libero_three/prepare_context.py \
  --benchmark libero_long_plus_plus \
  --source /path/to/efficiency_aligned_v12 \
  --destination ../work/libero_three/longpp-icl

python scripts/libero_three/prepare_context.py \
  --benchmark libero_ultra_long \
  --source /path/to/efficiency_aligned_v12 \
  --destination ../work/libero_three/ultra-icl

python scripts/libero_three/prepare_context.py \
  --benchmark libero_pro \
  --source /path/to/pro_safe_carry_v19 \
  --destination ../work/libero_three/pro-icl
```

## 一次性依赖审计

在分配模拟器前执行：

```bash
python scripts/libero_three/check_source_runtime.py \
  --runtime-config ../work/libero_three/source-runtime.afs.json \
  --probe-python
```

该命令检查三套 Python、源码与资产目录、密钥非空、checkpoint 大小/哈希、tokenizer
哈希、全部 ICL manifest/package 哈希、12/9/80 映射数量、Agent config fingerprint、
工具 URL，并实际探测每套 Python 的关键导入、PRO 80 个选定初态和 BDDL。任一外部依赖
缺失会在启动评测前失败。

## Agent wheel 导出与仓库外安装

每个叶子 preset 都可独立导出。下面以 Long++ 为例，另外两套替换 preset 和 bundle
名称即可：

```bash
python -m heart_runtime.agents.package \
  --config configs/agents/libero_three/long_plus_plus_v13.yaml \
  --name libero_long_plus_plus_v13 \
  --output /tmp/libero-longpp-agent-build
python -m build --wheel /tmp/libero-longpp-agent-build
python -m pip install /tmp/libero-longpp-agent-build/dist/*.whl
```

安装后可从仓库外使用 `--agent-config bundle:libero_long_plus_plus_v13`。ICL 本体不进入
wheel，仍由 `HEART_LIBERO_LONGPP_ICL_ROOT` 指向经过哈希校验的外部包；Ultra-Long 和
PRO 对应 `HEART_LIBERO_ULTRA_ICL_ROOT` 和 `HEART_LIBERO_PRO_ICL_ROOT`。wheel 声明
`heart-runtime[runtime]`，应与本交付对应的 HEART commit 一起构建和安装。

## 源码 smoke 与子集运行

Long++/Ultra-Long 单案例 smoke：

```bash
python scripts/libero_three/run_source.py \
  --runtime-config ../work/libero_three/source-runtime.afs.json \
  --benchmark libero_long_plus_plus \
  --task t00-i01 \
  --results-root ../work/libero_three/source-smoke/longpp-t00 \
  --run-id longpp-t00-smoke \
  --port 19081
```

完整迁移子集：

```bash
python scripts/libero_three/run_source_subset.py \
  --runtime-config ../work/libero_three/source-runtime.afs.json \
  --benchmark libero_long_plus_plus \
  --results-root ../work/libero_three/source-repro/longpp \
  --run-id longpp-v13-icl \
  --max-concurrent 4
```

将 `--benchmark` 换成 `libero_ultra_long` 或 `libero_pro` 即可。仓库 context map 是
权威案例列表，分别固定为 12、9、80。重复传 `--task` 可只跑 smoke，不需要另建任务列表。
子集 runner 会自动为 PRO 选择 native toolkit runner，为另外两套选择 Benchmark service；
每个案例保留独立日志，根目录生成含成功率和平均原生分数的 `summary.json`。PRO 配置将
`manage_local_services` 设为 `true` 时，runner 会自动启停 `vla_rpc_url` 和
`sam3_rpc_url` 对应的本地 Pi0.5/SAM3 服务；只有使用外部托管服务时才设为 `false`。两份
checkpoint 路径也由同一配置声明，不存在代码内隐藏路径。

标准 registry/镜像入口使用以下叶子 preset：

| Benchmark | Agent preset |
| --- | --- |
| Long++ | `configs/agents/libero_three/long_plus_plus_v13.yaml` |
| Ultra-Long | `configs/agents/libero_three/ultra_long_v13.yaml` |
| PRO | `configs/agents/libero_three/pro_v19.yaml` |

只有 `success` 与原生 `task_failure` 是合法评测终态。Agent error、基础设施错误、缺少
`result.json` 或重复结果都会使命令失败。Smoke 的目标是验证链路，因此得到带完整证据的
`task_failure` 也表示运行链路通过，不代表任务得分成功。

## 输出与验收

每个案例应保存：

- `result.json`：HEART 终态、1× 原生分数和固定 provenance；
- `native/score.json`：1× 快照、累计诊断及真实步数；
- `native/episode.mp4`：存在帧时的相机证据；
- `media/`：返回给 Agent 的内容寻址观测；
- `runner_trace/`：task/action/feedback envelope；
- Agent trace 与去除凭证值后的 `agent-config.json`。

验收要求计划数严格为 12、9、80，所有案例都有合法终态，无 Agent/基础设施错误，原生
证据可读，benchmark/source/config/package 哈希符合锁定值。模型工具可能非确定，因此
分数一致只是证据之一，不是唯一验收门槛。

## 镜像边界

当前源码复现不依赖新构建镜像。以后在其他机器构建时，可用：

```bash
python -m benchmarks.package --benchmark libero_pro \
  --output ../work/libero_three/build-pro
python -m benchmarks.package --benchmark libero_lilo \
  --output ../work/libero_three/build-lilo
python -m benchmarks.libero_pro.assets \
  --source /path/to/full-evaluation/libero/libero \
  --output-dir ../work/libero_three/registry/libero_pro/assets
```

构建上下文仍放在外部 `work/`。最终镜像必须以 digest 固定；镜像只含 benchmark 和
模拟器，不能含 Agent SDK、模型凭证或对话状态。Pi0.5/SAM3 属于 Agent/模型服务边界，
不放进 Benchmark 镜像。

PRO manifest 必须通过 `--asset ../work/libero_three/registry/libero_pro/assets/asset.json`
声明上述资产。准备器仅密封 `bddl_files/` 与 `init_files/`，固定目录 SHA-256 为
`381f91eec4ec26bc2a0bd06e32da8713f56367c5431d7a8cfa74d69439b57be9`，约 18.2 MB；
运行时以只读方式挂到 `/heart/assets/libero_pro`。两个镜像都会在可写 `/tmp` 中生成
LIBERO 路径配置，避免只读容器启动时写源码目录，也避免 PRO 回退到不完整的内置评测文件。
在构建后的镜像内生成 PRO manifest 时，也要把 registry 的 `libero_pro/` 目录读写挂载到
同名路径，并把其中密封的 snapshot 只读挂载到 `/heart/assets/libero_pro`。

当前没有可拉取的最终镜像地址和 digest，因此“已构建 Benchmark 镜像”是本交付唯一明确
未完成项。Dockerfile、固定基础镜像 digest、上游 commit、构建上下文导出器和 manifest
生成器已经入库；在镜像构建机完成 build/push 后，仍需把最终
`repository@sha256:digest` 回填到两个 Benchmark README，并从该镜像执行原生 HTTP smoke。

在未实际 build 的前提下，只能给容量规划值而不能冒充最终 registry 大小。当前 AFS
实测：普通 LIBERO 源码树约 427 MiB（其中 assets 405 MiB），LIBERO-PRO checkout 约
657 MiB（assets 617 MiB），robosuite 自带 assets 约 590 MiB。再加 CPU Torch、MuJoCo、
SciPy、基础 Python 和系统库，预计：

| 镜像 | `docker images` 解压后估算 | registry/pull 压缩量估算 |
| --- | ---: | ---: |
| `libero_lilo`（Long++ 与 Ultra 共用） | 2.4–3.0 GiB | 1.2–1.8 GiB |
| `libero_pro` | 3.0–4.0 GiB | 1.5–2.4 GiB |
| 两个镜像合计 | 5.4–7.0 GiB | 2.7–4.2 GiB |

建议目标机给最终镜像预留至少 8 GiB，构建机给 build cache 和中间层预留 15–20 GiB。
Pi0.5 的 7.47 GB 权重、SAM3 的 3.45 GB 权重、ICL 和模型服务 Python 环境不属于
Benchmark 镜像；若错误地把两个 checkpoint 打入镜像，仅原始权重就会额外增加约
10.9 GB。最终数值必须在构建机上用 `docker image inspect` 和 registry manifest 实测。

## 安全规则

- 不提交 `work/`、凭证、checkpoint、复制的 ICL、dataset、私有 registry manifest、
  视频和结果；
- 参考评测目录只读；
- 报告中的源码 revision、配置 fingerprint、package 哈希和镜像 digest 必须不可变；
- Benchmark 服务拥有模拟器文件和原生分数，Agent 不得写入这些结果；
- adapter/scorer 变化后必须重新构建镜像并生成 manifest；源码模式也必须重新完成 smoke
  和依赖审计。
