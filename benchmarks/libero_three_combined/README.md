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

The `v1.0.1-egl` images were built from RoboRSI commit
`5b8c7f7aa6e1b67119ef3e887625601387ce917e` and pulled back from GHCR by digest:

```bash
LONGPP_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-long-plus-plus@sha256:814139261e914b114cb89a359c6a39d4f409a556f79928e986b6ade3dfe7dc7a'
ULTRA_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-ultra-long@sha256:814139261e914b114cb89a359c6a39d4f409a556f79928e986b6ade3dfe7dc7a'
PRO_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-pro@sha256:a83417f1459a4c555c457caa82ef00a5de50191e3d8deb943894fa9285cff172'
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

For the fixed 12/9/80 subsets, use `--entrypoint python` and pass
`-B /opt/roborsi/scripts/libero_three/run_combined_subset.py` immediately after
the image reference. The runner defaults to 16 concurrent cases and one shared
GPU. It preserves every attempt and reuses a result only after matching the
image/code, Agent, ICL, model endpoint and timeout fingerprint, the previous
zero process exit, task/seed identity, and the native score file digest. It
exits nonzero while any case lacks a verified native terminal result.
