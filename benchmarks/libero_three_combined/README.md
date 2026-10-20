# Three-LIBERO single-image deployment

This deployment wrapper is for schedulers that accept only one container image
per job. It combines one locked three-LIBERO Agent image with either the LiLo or
PRO Benchmark image. Long++ and Ultra-Long use the LiLo build; PRO uses the PRO
build. Each evaluation job therefore starts exactly one image.

The image contains the native Benchmark, all three Agent bundles, sealed ICL
packages, tokenizer and Python dependencies. It does not contain model weights,
an API endpoint or credentials. The model API key remains a read-only runtime
secret and results use a writable runtime mount.

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
  roborsi-libero-lilo-combined:local \
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
