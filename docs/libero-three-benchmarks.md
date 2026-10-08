# LIBERO-PRO, Long++ and Ultra-Long

This integration keeps simulator state and native scoring in standalone HEART
Benchmark services. The Agent receives only declared observations and submits
either 7-DoF Panda `OSC_POSE` actions or one of the declared feedback primitives
(`move_to`, `move_pose`, wrist rotation, gripper control). Primitives compile to
physical 7-DoF actions inside the Benchmark and every physical step counts
toward the same budget. A single Agent dialogue persists for the whole episode,
including an optional failure-only continuation.

## Evaluation contracts

| Benchmark | Full set | Migration subset | Official 1× | Primary score |
| --- | ---: | ---: | ---: | --- |
| LIBERO-PRO Task/Swap | 8 suites × 10 tasks × 10 states = 800 | 80 tasks, fixed state 3 | 10,000 physical steps | final-goal success |
| LIBERO-Long++ | 12 configurations × 10 bare-reset trials = 120 | 12 configurations, fixed state 1 | 200 × ordered skills | ordered-prefix fraction; all skills for success |
| LIBERO-Ultra-Long | 9 configurations × 10 bare-reset trials = 90 | 9 configurations, fixed state 1 | 200 × ordered skills | ordered-prefix fraction; all skills for success |

`plus9_on_failure` defaults to false. When enabled, only a case that failed at
the official 1× boundary may continue, in the same environment and Agent
dialogue, up to 10× total physical steps. `result.json` and aggregate scores
always use the immutable 1× snapshot. `native/score.json` additionally records
cumulative recovery and the actual physical/decision step counts.

Long++ and Ultra-Long repeat labels are not random seeds. The official profile
performs the released bare random reset ten times; the deterministic migration
profile explicitly records fixed state 1. Their scorer advances only the
uninterrupted released skill order and never substitutes LIBERO final-goal
success for ordered success.

Both ordered benchmarks declare the historical
`lilo-instance-pose-feedback-v1` observation contract. Each observation includes
`instance_pose_feedback`: exact registered instance names, live world positions,
collision-geometry top/bottom heights, exact gripper contacts, held objects and
the current ordered skill/progress. This channel is read-only and never calls or
advances the scorer. It is intentionally part of the named evaluation condition;
do not combine these results with older vision-only runs.

The migration also preserves `libero-robot-state-feedback-v1`. Every ordered
observation names the `robot0_eef_pos`, xyzw quaternion, and
`robot0_gripper_qpos` values returned by the legacy v13 direct tools while
retaining the compact eight-dimensional `states` policy input. The
`heart_action` schema describes each legacy direct-control primitive explicitly;
in particular, `rotate_wrist` rotates in place and is not interchangeable with
`move_pose.target_yaw`. This compatibility layer does not change tasks, scoring,
initialization, or physical-step budgets.

The historical comparison labels are easy to confuse: the Long++ and
Ultra-Long subset reported with the full study is the v13 no-tool,
token-accurate condition. The v21 PRO full-800 run extends the v18 persistent
memory policy across states 0--9; its representative 80-case subset is v18 at
fixed state 2. The currently supplied PRO preset/packages reproduce the later
v19 safe-carry subset at fixed state 3, so those PRO numbers are not a direct
subset comparison for v21.

## Delivery results and evidence

All rows below used the real model and simulator at the official 1x boundary,
without `plus9_on_failure`. The Long++ and PRO diagnostic aggregates combine
later valid strict-1x retries with the first pass and are not single clean
passes. Ultra-Long is one complete same-condition pass assembled from parallel
shards.

| Benchmark / condition | Cases | Success | Mean native score | Internal evidence below `../work/libero_three/` |
| --- | ---: | ---: | ---: | --- |
| Long++ v13, state 1, first pass | 12 x 1 | 9/12 | 0.9375 | `source-repro-v3/libero_long_plus_plus/summary.json` |
| Long++ v13, diagnostic aggregate | 12 x 1 | 12/12 | 1.0000 | `source-longpp-best-valid-v1/summary.json` |
| Ultra-Long v13, state 1, clean pass | 9 x 1 | 8/9 | 0.9583 | `source-v13-compat-geom-full-r3/summary.json` |
| PRO v19, state 3, first pass | 80 x 1 | 72/80 | 0.9000 | `source-pro-combined-v1/summary.json` |
| PRO v19, diagnostic aggregate | 80 x 1 | 76/80 | 0.9500 | `source-pro-best-valid-v1/summary.json` |

The frozen internal references are 12/12 Long++, 8/9 Ultra-Long and 75/80 PRO
v19 at state 3. PRO v21's 756/800 follows the v18 persistent-memory policy and
uses state 2 for its representative subset, so it is not directly comparable
to this v19/state-3 delivery. The upstream [LiLo-VLA](https://github.com/YY-GX/LiLo-VLA),
[LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO), and
[LIBERO-PRO](https://github.com/RLinf/LIBERO-PRO) projects do not publish scores
under this exact subset, Agent and budget combination; no unmatched public
number is guessed or ranked here.

Representative success/failure case directories are `t00-i01` / `t02-i01`
under `source-repro-v3/libero_long_plus_plus/cases/`, `t00-i01` / `t01-i01`
under `source-v13-compat-geom-full-r3/cases/`, and
`libero_10_swap-t00-i03` / `libero_10_swap-t06-i03` under
`source-pro-combined-v1/cases/`. Each retains `result.json`, native score and
video, Runner trace, full Agent trace and redacted effective configuration. The
aggregate-directory symlinks are convenience indexes; their targets own the
evidence files.

Observed first-pass wall-clock spans were about 27 minutes for Long++, 80
minutes for Ultra-Long and 2.3 hours for PRO under the recorded concurrency.
The traces contain 496/969/1923 model requests, about 8.0M/92.3M/41.6M input
tokens (including tokens later served from cache), and 159k/231k/147k output
tokens respectively. The internal endpoint has no delivery pricing, so a
currency cost cannot be stated; apply the selected endpoint's input, output and
cache rates to these counters.

## Inputs

An evaluation requires:

1. This repository checkout and the versioned files under
   `configs/libero_three/`.
2. A Benchmark runtime: either a digest-locked image/manifest or the pinned
   source checkouts and Python environment declared by a host runtime config.
3. Read-only LIBERO assets required by that Benchmark runtime.
4. A sealed ICL package tree. Every package contains `manifest.json`, a complete
   SHA-256 inventory and a `payload/`; undeclared files and links are rejected.
5. An OpenAI-compatible endpoint and a key file named only by the private host
   runtime config. Credentials are never stored in a repository config.
6. For PRO v19, Pi0.5 and SAM3 checkpoints, the pinned PaliGemma tokenizer
   under `OPENPI_DATA_HOME`, plus the model RPC endpoints. The
   historical Long++/Ultra-Long v13 condition disables both tools in the host
   config. MCP endpoint fields remain available for generic Agent-owned tools.

The Benchmark image has no model dependency or model credential. The Agent and
Benchmark may be deployed independently. VLA/SAM3 are Agent-owned MCP services;
their URLs are runtime environment values and are not recorded as secrets.
The generated manifests request one GPU for deterministic MuJoCo EGL rendering;
the model services do not share or inherit that device allocation.

## Build and lock Benchmark images

Run image builds on a builder, not a cluster login node:

```bash
python -m benchmarks.package --benchmark libero_pro \
  --output ../work/libero_three/build-pro
python -m benchmarks.package --benchmark libero_lilo \
  --output ../work/libero_three/build-lilo
python -m benchmarks.libero_pro.assets \
  --source /path/to/full-evaluation/libero/libero \
  --output-dir ../work/libero_three/registry/libero_pro/assets
```

Build and push both contexts, retain their `repository@sha256:digest` values,
then run these commands inside the corresponding image:

```bash
python -m benchmarks.libero_pro.manifest \
  --image REGISTRY/heart-libero-pro@sha256:DIGEST \
  --asset /output/libero_pro/assets/asset.json \
  --profile migration_subset \
  --output /output/libero_pro/manifest.json

python -m benchmarks.libero_lilo.manifest \
  --image REGISTRY/heart-libero-lilo@sha256:DIGEST \
  --benchmark libero_long_plus_plus --profile migration_subset \
  --output /output/libero_long_plus_plus/manifest.json

python -m benchmarks.libero_lilo.manifest \
  --image REGISTRY/heart-libero-lilo@sha256:DIGEST \
  --benchmark libero_ultra_long --profile migration_subset \
  --output /output/libero_ultra_long/manifest.json
```

The PRO asset command seals only `bddl_files/` and `init_files/`, requires the
full-evaluation directory SHA-256
`381f91eec4ec26bc2a0bd06e32da8713f56367c5431d7a8cfa74d69439b57be9`,
and produces an approximately 18.2 MB read-only Registry snapshot mounted at
`/heart/assets/libero_pro`. Both images materialize LIBERO's mutable path file
under `/tmp`; PRO therefore cannot silently fall back to incomplete checkout
evaluation files. When generating the PRO manifest inside the built image,
mount the registry's `libero_pro/` directory read-write at the same path and its
sealed snapshot read-only at `/heart/assets/libero_pro`.

Omit `--profile migration_subset` for the official full set. Add
`--plus9-on-failure` only for a separately named cumulative diagnostic. Never
compare a +9 run to a 1× run as if their stopping conditions were identical.

## Prepare the frozen ICL inputs

The preparation command reads an existing package family, verifies every file,
copies it to an external work directory, verifies it again, and emits a
diagnostic `package-map.json`. It never modifies the source. The authoritative
task-to-package maps remain in `configs/libero_three/`; canonical relocatable
Agent presets are in `configs/agents/libero_three/`.

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

Set `HEART_LIBERO_LONGPP_ICL_ROOT`, `HEART_LIBERO_ULTRA_ICL_ROOT`, and
`HEART_LIBERO_PRO_ICL_ROOT` to the corresponding external `packages/`
directories. The repository presets use low reasoning effort for PRO and max
for Long++/Ultra-Long, plus explicit Responses prompt caching and three bounded
retries for transient transport/5xx failures. Presets are tool-capable; the
host config explicitly disables VLA and SAM3 for the historical
Long++/Ultra-Long v13 condition.

The Long++/Ultra-Long presets also reproduce v13's token-accurate context
policy: a 1,050,000-token window, 128,000-token output reserve, 32,768-token
overhead reserve, 0.75 summary trigger, eight complete recent exchanges and two
image groups. `run_source.py` injects the host-configured local tokenizer and
its locked SHA-256. Text history remains complete below the trigger; this is
not equivalent to a fixed recent-turn truncation.

The supported leaf presets are
`configs/agents/libero_three/long_plus_plus_v13.yaml`,
`configs/agents/libero_three/ultra_long_v13.yaml`, and
`configs/agents/libero_three/pro_v19.yaml`. `base.yaml` and `v13.yaml` are
inheritance-only parents.

Export and install a relocatable Agent bundle, for example:

```bash
python -m heart_runtime.agents.package \
  --config configs/agents/libero_three/long_plus_plus_v13.yaml \
  --name libero_long_plus_plus_v13 \
  --output /tmp/libero-longpp-agent-build
python -m build --wheel /tmp/libero-longpp-agent-build
python -m pip install /tmp/libero-longpp-agent-build/dist/*.whl
```

Outside the checkout select `bundle:libero_long_plus_plus_v13`. The wheel
declares `heart-runtime[runtime]`; sealed ICL packages remain external and are
selected through the preset's named environment variable.

## Source runtime on an AFS-capable machine

Copy `configs/libero_three/source-runtime.example.json` outside the checkout and
fill in machine-visible paths. A complete private host config names the Agent
Python/wrapper, model endpoint and key file, three ICL roots, tool MCP URLs, and
the Benchmark Python/source/assets for each family. The public logical asset
contract is `configs/libero_three/assets.lock.json`; absolute AFS paths and
secrets deliberately stay in the private host config.

The PRO `pythonpath` entry must be the root of the pinned LIBERO-PRO checkout,
not its inner `libero/` directory. The required import is
`liberopro.liberopro`. Assets, BDDL files and init states are named
independently by the host config and may come from a separate frozen asset
bundle. A source evaluation does not read demonstrations, so a fresh PRO
checkout may legitimately have no `liberopro/datasets/` directory. Some
published pruned-init files can contain an empty set and some variant BDDL
files may fail to parse, so an evaluation config must point `init_states` and
`bddl_files` at the complete evaluation assets. Preflight loads and parses all
80 selected cases and rejects an empty or missing state or an invalid BDDL
before simulator allocation.

The intended portable AFS layout is:

```text
newrpent/
├── NewRPent/                 # this Git checkout only
└── work/libero_three/        # private host config, ICL packages, runtimes, logs/results
```

The checkout can therefore be replaced or rebased without touching large or
private runtime state. On another machine that mounts the same AFS tree, only
the checkout and the private host config are needed; every remaining external
path is named by that config. The machine/container still needs an Ubuntu
22.04-compatible `python3.10` and Linux EGL/GL runtime libraries (`libgl1`,
`libegl1`, and `libglib2.0-0`). The LiLo venv entry resolves to
`/usr/bin/python3.10`; mounting AFS alone is not enough on a host without that
interpreter. The configured environments or wrappers carry the Python package
dependencies.

`system_packages` records `python3.10` and those host/container libraries
explicitly. The
configured `openpi_data_home` must already contain
`big_vision/paligemma_tokenizer.model`; preflight checks its locked size and
digest so Pi0.5 startup never depends on downloading it from GCS.

Audit every referenced source tree, Python, ICL manifest, checkpoint, tokenizer,
key file, selected PRO initial state and BDDL before running:

```bash
python scripts/libero_three/check_source_runtime.py \
  --runtime-config ../work/libero_three/source-runtime.afs.json \
  --probe-python
```

Run one case without building an image:

```bash
python scripts/libero_three/run_source.py \
  --runtime-config ../work/libero_three/source-runtime.afs.json \
  --benchmark libero_long_plus_plus \
  --task t00-i01 \
  --results-root ../work/libero_three/source-smoke/longpp-t00 \
  --run-id longpp-t00-smoke \
  --port 19081
```

The command fails when the case ends in an Agent or infrastructure error; only
`success` and native `task_failure` are valid evaluation terminals.

Run the complete configured migration subset with the same host config:

```bash
python scripts/libero_three/run_source_subset.py \
  --runtime-config ../work/libero_three/source-runtime.afs.json \
  --benchmark libero_long_plus_plus \
  --results-root ../work/libero_three/source-repro/longpp \
  --run-id longpp-v13-icl \
  --max-concurrent 4
```

The repository context map is the authoritative case list (12 Long++, 9
Ultra-Long or 80 PRO). Repeating `--task` selects smoke cases without creating a
second task-list config. The subset runner keeps per-case logs and writes one
`summary.json` with success rate and mean native score; any invalid terminal
makes the command fail. It automatically
uses the standalone Benchmark service for Long++/Ultra-Long and the repository's
native LIBERO toolkit with shared Pi0.5/SAM3 RPC services for the frozen PRO v19
tool contract.

For PRO, set `manage_local_services` to `true` to let the subset runner start
and stop the local Pi0.5/SAM3 services named by `vla_rpc_url` and
`sam3_rpc_url`. Set it to `false` only when those endpoints are managed
externally. Both checkpoints are named by the same host config; no checkpoint
path is hidden in repository code.

## One-command preflight and evaluation

Validate the fully expanded cases, image locks, package hashes and Agent inputs
before allocating a simulator:

```bash
python scripts/libero_three/run.py \
  --benchmark libero_long_plus_plus \
  --registry-root ../work/libero_three/registry \
  --agent-config configs/agents/libero_three/long_plus_plus_v13.yaml \
  --results-root ../work/libero_three/results \
  --run-id longpp-v13-icl \
  --agent-set parameters.enable_vla=false \
  --agent-set parameters.enable_sam3=false \
  --dry-run
```

Remove `--dry-run` to execute locally. On SenseCore, add `--sco-config` so the
existing HEART SCO executor creates Benchmark workers; do not run MuJoCo,
models, image builds, or long evaluations on a login node. `--resume-from`
reuses only completed non-retryable cases whose complete locked inputs match.

The migration validation order is Long++ (12), Ultra-Long (9), then PRO (80).
It is an ICL-only migration check. It validates protocol alignment, terminal
coverage, native scores, traces and media; without a newly run no-ICL arm it
must not be described as a causal ICL improvement.

## Outputs and acceptance

Keep downloaded/copied assets, generated inputs, caches and outputs outside the
checkout, for example below the sibling `../work/libero_three/` directory. Each
case contains:

- `result.json`: HEART status, 1× native score and pinned provenance;
- `native/score.json`: 1× snapshot plus cumulative diagnostics;
- `native/episode.mp4`: streamed camera evidence when frames are available;
- `media/`: content-addressed observations returned to the Agent;
- `runner_trace/`: task/action/feedback envelopes;
- Agent trace and `agent-config.json`: selected model, package inputs and source
  fingerprint, without credential values.

Acceptance requires exactly 12, 9 and 80 planned subset cases, no missing
terminal record, no infrastructure/Agent error, readable native evidence and
the expected benchmark/source/config hashes. Score equality is useful evidence
but is not the sole gate because model services can be nondeterministic.

## Security and release rules

- Do not commit `work/`, credentials, model checkpoints, copied ICL packages,
  datasets, generated manifests tied to private registries, or result videos.
- Keep all source pins and image digests immutable for a reported run.
- Treat reference evaluation directories as read-only inputs.
- A Benchmark service owns simulator files and native score; an Agent cannot
  write either result.
- Rebuild the image and regenerate its manifest after any adapter or scorer
  change. Source-digest verification rejects undeclared runtime files.

No pullable final image reference or digest is currently available. That is
the sole explicit incomplete delivery item. The Dockerfiles, pinned base image
digest, upstream commits, context exporter and manifest generators are present;
after build/push, record `repository@sha256:digest` in each Benchmark README and
run the native HTTP smoke from those exact images.

Until a real build exists, size is a capacity estimate rather than a registry
fact. Measured source inputs are about 427 MiB for LIBERO (405 MiB assets), 657
MiB for the LIBERO-PRO checkout (617 MiB assets), and 590 MiB for robosuite's
assets. With CPU Torch, MuJoCo, SciPy, Python and system libraries, expect about
2.4--3.0 GiB unpacked / 1.2--1.8 GiB compressed for `libero_lilo`, and
3.0--4.0 GiB unpacked / 1.5--2.4 GiB compressed for `libero_pro`. Budget at
least 8 GiB to hold both final images and 15--20 GiB on the builder for cache
and intermediate layers. Pi0.5 (7.47 GB) and SAM3 (3.45 GB) checkpoints are
outside the Benchmark images; embedding them would add about 10.9 GB of raw
weights alone. Confirm final values with image inspection and the registry
manifest after the actual build.
