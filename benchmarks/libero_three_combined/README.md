# Three-LIBERO combined deployment

[简体中文](README.zh-CN.md) · [Full deployment guide](../../docs/libero-three-reproduction.md)

This image combines one verified three-LIBERO Agent image with either the LiLo
or PRO Benchmark image. Long++ and Ultra-Long share the LiLo composition. It
supports schedulers that accept one image per job, with separate Agent and
native Python package directories inside the image.

## Published images

The following immutable GHCR artifacts were published in upstream PR 93 from
commit `5b8c7f7aa6e1b67119ef3e887625601387ce917e`. They retain their original
embedded presets. See the full guide to rebuild the current source and select
a model ID supported by your endpoint.

```bash
export LONGPP_COMBINED_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-long-plus-plus@sha256:814139261e914b114cb89a359c6a39d4f409a556f79928e986b6ade3dfe7dc7a'
export ULTRA_COMBINED_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-ultra-long@sha256:814139261e914b114cb89a359c6a39d4f409a556f79928e986b6ade3dfe7dc7a'
export PRO_COMBINED_IMAGE='ghcr.io/opensensenova/sensenova-roborsi-libero-pro@sha256:a83417f1459a4c555c457caa82ef00a5de50191e3d8deb943894fa9285cff172'
docker pull "$LONGPP_COMBINED_IMAGE"
docker pull "$ULTRA_COMBINED_IMAGE"
docker pull "$PRO_COMBINED_IMAGE"
```

## Run one case

Set `RUN_ROOT`, `MODEL_API_KEY_FILE` and `OPENAI_BASE_URL` to your output root,
private key file and model endpoint. Use a new single-case output directory.

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

The default entrypoint is `run_combined.py`. For the 12/9/80 subsets use
`--entrypoint python` and pass
`-B /opt/roborsi/scripts/libero_three/run_combined_subset.py` after the image
reference. The [full guide](../../docs/libero-three-reproduction.md) includes
the complete command and verified result-reuse behavior.

## Rebuild

Build the three installed Agent bundles and native Benchmark images using the
[public-input rebuild steps](../../docs/libero-three-reproduction.md). Set
`AGENT_IMAGE`, `LILO_IMAGE` and `PRO_IMAGE` to those actual repository digests,
and choose new combined tags. From the repository root:

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

Model credentials are runtime inputs. The combined mode shares a container
between Agent and Benchmark; use separate images with `bench eval` when each
case needs an independent Agent filesystem. Preserve the source revision and
both input digests with the new output digest.

[Upstream validation](../../docs/libero-three-subset-validation.md) records
PR 93's historical real-model runs. This migration has not rebuilt or rerun
those GPU/model experiments.
