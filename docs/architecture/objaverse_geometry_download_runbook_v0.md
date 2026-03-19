# Objaverse Geometry Download Runbook v0

This runbook documents the first real geometry-download step for Objaverse
furniture in `vgm-assets`.

It is intentionally narrow and only targets the accepted shortlist from:

- `sources/objaverse/selective_geometry_manifest_objaverse_000_014_v0.json`

## Official Download Method

For Objaverse 1.0, the supported Python API is `objaverse.load_objects(...)`.

We use that API to download only the shortlisted object UIDs, then copy the
resulting mesh payloads into the canonical `RAW_DATA_ROOT` layout used by
`vgm-assets`.

## One-Time Environment Step

Install the Objaverse client into the `vgm-assets` micromamba environment:

```bash
./scripts/env/install_objaverse_support.sh
```

If you use a different env name:

```bash
./scripts/env/install_objaverse_support.sh my-env-name
```

## Selective Download

Run the current shortlist download with:

```bash
./scripts/sources/download_objaverse_selective_geometry_000_014_v0.sh
```

Optional flags are forwarded to the Python CLI, for example:

```bash
./scripts/sources/download_objaverse_selective_geometry_000_014_v0.sh \
  --download-previews \
  --notes "first selective Objaverse geometry pull"
```

You can also control process count through the environment:

```bash
export VGM_ASSETS_OBJAVERSE_DOWNLOAD_PROCESSES=4
./scripts/sources/download_objaverse_selective_geometry_000_014_v0.sh
```

## Output Layout

Downloaded raw payloads are copied into:

- `RAW_DATA_ROOT/sources/objaverse/furniture_v0/geometry/<object_uid>/raw/`

Each successful candidate gets:

- `model.glb` or `model.<downloaded suffix>`
- optional preview image
- `source_manifest.json`

The batch also writes:

- `RAW_DATA_ROOT/sources/objaverse/furniture_v0/geometry/objaverse_000_014_selective_geometry_v0_download_manifest.json`

## Notes

- this step still does not normalize the meshes
- it only registers raw geometry payloads in the canonical storage layout
- if a UID does not resolve to a local download, it is recorded as
  `missing_download` in the batch manifest
