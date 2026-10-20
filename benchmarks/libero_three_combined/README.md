# Three-LIBERO single-image deployment

This deployment wrapper is for schedulers that accept only one container image
per job. It combines one locked three-LIBERO Agent image with either the LiLo or
PRO Benchmark image. Long++ and Ultra-Long use the LiLo build; PRO uses the PRO
build. Each evaluation job therefore starts exactly one image.

The image contains the native Benchmark, all three Agent bundles, sealed ICL
packages, tokenizer and Python dependencies. It does not contain model weights,
an API endpoint or credentials. The model API key remains a read-only runtime
secret and results use a writable runtime mount.

## Published images

The `v1.0.0-egl` images were built from RoboRSI commit
`281dc19296fbe2a4c5a7f01b8fc265529a5e0754` and pulled back from GHCR by digest:

```bash
LONGPP_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-long-plus-plus@sha256:4463b6a247617a51653e1b170cc1cbcbae1a2c773a06f21afdf8626aea5a11c9'
ULTRA_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-ultra-long@sha256:4463b6a247617a51653e1b170cc1cbcbae1a2c773a06f21afdf8626aea5a11c9'
PRO_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-pro@sha256:fd84be8ca67100624dac4a3ddf0de06e74e46c5d1d1b7c8088e6e0713fe70e29'
```

Long++ and Ultra-Long have separate Benchmark packages as required by the
registry convention, but intentionally share identical LiLo-native image
content. The `egl` suffix records the headless NVIDIA EGL rendering boundary;
the images do not ship a CUDA toolkit.

This is a deployment composition, not a replacement for the independently
attested Benchmark and Agent recipes. Build it from the repository root because
it overlays the reviewed RoboRSI source and runners:

```bash
docker build -f benchmarks/libero_three_combined/Dockerfile \
  --build-arg AGENT_IMAGE=repository/agent@sha256:DIGEST \
  --build-arg BENCHMARK_IMAGE=repository/libero-lilo@sha256:DIGEST \
  --build-arg ROBORSI_REVISION="$(git rev-parse HEAD)" \
  -t roborsi-libero-lilo-combined:local .
```

Use the PRO Benchmark digest to build the PRO image. Run one case with:

```bash
docker run --rm --gpus all \
  -v /path/to/model_api.key:/run/secrets/model_api.key:ro \
  -v /path/to/results:/results \
  "$LONGPP_IMAGE" \
  --benchmark libero_long_plus_plus --task t00-i01 \
  --run-id longpp-smoke --results-root /results/longpp-smoke \
  --api-key-file /run/secrets/model_api.key \
  --base-url https://your-responses-endpoint.example/v1
```

For the fixed 12/9/80 subsets, override the entrypoint with
`/opt/roborsi/scripts/libero_three/run_combined_subset.py`. The runner defaults
to 16 concurrent cases and one shared GPU, preserves every attempt, reuses only
cases with a native `success` or `task_failure`, and exits nonzero while any case
lacks a legal terminal result.
