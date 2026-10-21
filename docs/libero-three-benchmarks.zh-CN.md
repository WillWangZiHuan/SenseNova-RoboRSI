# LIBERO-PRO、Long++ 与 Ultra-Long

[English](libero-three-benchmarks.md) · [全部指南](README.md)

三套 benchmark 服务保留原生仿真与评分。专用 Agent 预设为每个任务绑定已验证的 ICL
package，在整个 episode 中保持同一段对话，并通过锁定的 tokenizer 管理上下文。
[部署指南](libero-three-reproduction.zh-CN.md)包含公开 combined 镜像的使用方式，
以及独立 Benchmark/Agent 镜像的重建步骤。

## 评测契约

| Benchmark | 官方全集 | 固定子集 | 官方 1× 预算 | 主评分 |
| --- | --- | --- | --- | --- |
| LIBERO-PRO Task/Swap | 8 个 suite × 10 个任务 × 10 个状态 = 800 | 80 个任务，state 3 | 10,000 物理步 | 最终目标成功 |
| LIBERO-Long++ | 12 个配置 × 10 次 bare-reset trial = 120 | 12 个配置，state 1 | 200 × 有序技能数 | 有序前缀比例；全部技能完成才成功 |
| LIBERO-Ultra-Long | 9 个配置 × 10 次 bare-reset trial = 90 | 9 个配置，state 1 | 200 × 有序技能数 | 有序前缀比例；全部技能完成才成功 |

Long++ 和 Ultra-Long 的 trial 标签不是随机种子。官方 profile 重复执行已发布的
bare random reset；`migration_subset` 明确采用固定 state 1。PRO 子集采用固定
state 3。所提供的 ICL map 覆盖这 12/9/80 个子集 case；运行全集时，Agent 的任务
覆盖范围需与所选 manifest 匹配。

Agent 可提交 7-DoF Panda `OSC_POSE` 动作，或已声明的反馈 primitive，包括
`move_to`、`move_pose`、腕部旋转和夹爪控制。Benchmark 将 primitive 转为物理动作，
每个物理步都计入同一预算。`rotate_wrist` 表示原地旋转，与 `move_pose.target_yaw`
的语义不同。

有序 benchmark 的 `lilo-instance-pose-feedback-v1` 提供注册实例名、实时世界坐标、
碰撞几何高度、精确夹爪接触、持有物体和当前技能进度，读取不会推进评分器。
`libero-robot-state-feedback-v1` 提供 `robot0_eef_pos`、xyzw 四元数和
`robot0_gripper_qpos`，同时保留紧凑的八维 `states`。这些反馈通道属于所命名的评测
条件，比较结果时需要保持一致。

`plus9_on_failure` 默认关闭。启用后，1× 边界失败的 case 可在同一环境和对话中继续，
最多执行 10× 总步数。`result.json` 与汇总始终保留不可变的 1× 分数；
`native/score.json` 另外记录累计恢复、物理步数和决策步数。有序评分遵循不间断的
已发布技能顺序，不用最终目标成功替代。

## Agent 预设与输入

| `configs/agents/libero_three/` 下的预设 | 安装后的 bundle | ICL package 数 |
| --- | --- | ---: |
| `long_plus_plus_v13.yaml` | `bundle:libero_long_plus_plus_v13` | 12 |
| `ultra_long_v13.yaml` | `bundle:libero_ultra_long_v13` | 9 |
| `pro.yaml` | `bundle:libero_pro` | 40，供 80 个 case 共用 |

`base.yaml` 和 `v13.yaml` 提供公共设置。三个叶子预设均使用 max reasoning 和精确
Token 计数策略：1,050,000-token 窗口、128,000-token 输出预留、32,768-token
额外预留、0.75 摘要触发比例、最近八组完整交换和两组图片。未达到阈值时保留完整历史。
PRO 允许 100 个模型轮次、5,000 秒 planner 预算，关闭模型重试；有序任务预设允许
10,000 个轮次、43,200 秒 planner 预算，并保留三次有界传输重试。

当前预设使用模型 ID `gpt-6-astra`。在预设或 `roborsi.agents.package --set` 中选择
服务支持的 ID；独立 Docker Agent 也支持 `bench eval --agent-set`。导出可移植 bundle
时，tokenizer 路径必须指向镜像内已验证的文件。

[资产锁](../configs/libero_three/assets.lock.json)标识 61 个 sealed ICL package
与 tokenizer；[context map](../configs/libero_three/context_maps/)将任务映射到
package。`prepare_agent_assets.py` 在复制前验证完整清单与哈希；构建 Agent 镜像时，
`verify_agent_image.py` 再对安装后的 bundle 执行相同检查。
[重建步骤](libero-three-reproduction.zh-CN.md)从公开 GHCR 镜像取得这些输入。

## 结果与溯源

每个完成的 case 记录 `result.json`、原生评分、可用的原生视频、内容寻址观测、
Runner 消息和 Agent trace/config 指纹。运行记录应保留镜像摘要、源码 revision、
manifest、模型 endpoint 标识与预算。`success` 和原生 `task_failure` 属于有分数
的终态；基础设施与 Agent 错误需单独统计。

[子集验证记录](libero-three-subset-validation.zh-CN.md)保留上游 PR 93 报告的真实
模型结果。该结果和公开镜像属于对应上游 revision。本次迁移未重新执行 Docker 构建、
GPU 仿真或模型评测。
