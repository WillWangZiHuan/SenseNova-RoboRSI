# LIBERO-PRO, Long++ and Ultra-Long

[简体中文](libero-three-benchmarks.zh-CN.md) · [All guides](README.md)

The three benchmark services retain native simulation and scoring. Their
specialized Agent presets bind a verified ICL package to each task, preserve
one dialogue throughout the episode and use a locked tokenizer for context
management. The [deployment guide](libero-three-reproduction.md) covers the
published combined images and rebuilding separate Benchmark and Agent images.

## Evaluation contracts

| Benchmark | Official set | Fixed subset | Official 1× budget | Primary score |
| --- | --- | --- | --- | --- |
| LIBERO-PRO Task/Swap | 8 suites × 10 tasks × 10 states = 800 | 80 tasks, state 3 | 10,000 physical steps | Final-goal success |
| LIBERO-Long++ | 12 configurations × 10 bare-reset trials = 120 | 12 configurations, state 1 | 200 × ordered skills | Ordered-prefix fraction; all skills for success |
| LIBERO-Ultra-Long | 9 configurations × 10 bare-reset trials = 90 | 9 configurations, state 1 | 200 × ordered skills | Ordered-prefix fraction; all skills for success |

Long++ and Ultra-Long trial labels are not random seeds. The official profile
repeats the released bare random reset; `migration_subset` explicitly uses
fixed state 1. PRO's subset uses fixed state 3. The supplied ICL maps cover
these 12/9/80 subset cases. Full-set evaluation needs an Agent whose task
coverage matches the chosen manifest.

An Agent may submit 7-DoF Panda `OSC_POSE` actions or the declared feedback
primitives, including `move_to`, `move_pose`, wrist rotation and gripper control.
The Benchmark compiles primitives to physical actions, and every physical step
uses the same budget. `rotate_wrist` rotates in place; its semantics differ
from `move_pose.target_yaw`.

For the ordered benchmarks, `lilo-instance-pose-feedback-v1` supplies registered
instance names, live world positions, collision-geometry heights, exact gripper
contacts, held objects and current skill progress. Reading it does not advance
the scorer. `libero-robot-state-feedback-v1` exposes `robot0_eef_pos`, xyzw
quaternion and `robot0_gripper_qpos`, alongside the compact eight-dimensional
`states` input. These feedback channels are part of the named evaluation
condition and must be retained when comparing results.

`plus9_on_failure` defaults to false. When enabled, a case that fails at 1× may
continue in the same environment and dialogue up to 10× total steps.
`result.json` and aggregates keep the immutable 1× score;
`native/score.json` additionally records cumulative recovery and physical and
decision step counts. Ordered scoring follows the uninterrupted released skill
order; it does not substitute final-goal success.

## Agent presets and inputs

| Preset under `configs/agents/libero_three/` | Installed bundle | ICL packages |
| --- | --- | ---: |
| `long_plus_plus_v13.yaml` | `bundle:libero_long_plus_plus_v13` | 12 |
| `ultra_long_v13.yaml` | `bundle:libero_ultra_long_v13` | 9 |
| `pro.yaml` | `bundle:libero_pro` | 40 shared across 80 cases |

`base.yaml` and `v13.yaml` supply shared settings. All three leaf presets use
max reasoning and the token-accurate context policy: 1,050,000-token window,
128,000-token output reserve, 32,768-token overhead reserve, 0.75 summary
trigger, eight complete recent exchanges and two image groups. History remains
complete below the trigger. PRO permits 100 model turns, a 5,000-second planner
budget and no model retries; the ordered presets permit 10,000 turns, a
43,200-second planner budget and three bounded transport retries.

The current preset uses model ID `gpt-6-astra`. Select an ID supported by your
endpoint in the preset or with `roborsi.agents.package --set`; an independent
Docker Agent also accepts `bench eval --agent-set`. Tokenizer paths must point
to the verified in-image file when exporting a portable bundle.

The [asset lock](../configs/libero_three/assets.lock.json) identifies the 61
sealed ICL packages and tokenizer. The
[context maps](../configs/libero_three/context_maps/) bind tasks to packages.
`prepare_agent_assets.py` verifies inventories and hashes before copying them;
`verify_agent_image.py` repeats the checks against installed bundles during the
Agent image build. The [rebuild procedure](libero-three-reproduction.md) obtains
these inputs from the published GHCR image.

## Results and provenance

Each completed case records `result.json`, native score, available native video,
content-addressed observations, Runner envelopes and the Agent trace/config
fingerprint. Keep the image digests, source revision, manifest, model endpoint
identity and budgets with the run. `success` and native `task_failure` are
scored terminals; infrastructure and Agent errors require separate reporting.

The [subset validation record](libero-three-subset-validation.md) preserves the
real-model results reported by upstream PR 93. Those results and published
images belong to that upstream revision. This migration has not rerun the
Docker builds, GPU simulations or model evaluations.
