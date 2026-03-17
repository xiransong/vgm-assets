# Poly Haven Room-Surface Manifests v0

This note defines the first raw-source and normalized-bundle manifest shapes
for one Poly Haven room-surface material in `vgm-assets`.

## Scope

This is a single-material vertical slice for the room-surface material track.

It defines:

- raw `source_manifest.json`
- processed `bundle_manifest.json`

It does not yet define:

- bulk download orchestration
- full room-surface material catalog export

## Raw Source Manifest

Each registered Poly Haven material should write:

```text
RAW_DATA_ROOT/
  sources/poly_haven/materials/<source_asset_id>/<resolution>_<format>/
    source_manifest.json
```

Minimal fields:

- `manifest_version`
- `source_id`
- `source_asset_id`
- `selection_id`
- `surface_type`
- `material_id`
- `source_url`
- `license`
- `preferred_resolution`
- `preferred_format`
- `raw_asset_rel_dir`
- `registered_at`
- `registered_by`
- `files`
- `missing_optional_files`

Each file record should include:

- `logical_name`
- `filename`
- `raw_relpath`
- `sha256`
- `size_bytes`

## Normalized Bundle Manifest

Each normalized room-surface material bundle should write:

```text
DATA_ROOT/
  materials/room_surfaces/poly_haven/<surface_type>/<material_id>/
    bundle_manifest.json
    source_metadata.json
```

Minimal `bundle_manifest.json` fields:

- `manifest_version`
- `bundle_id`
- `selection_id`
- `surface_type`
- `material_id`
- `display_name`
- `source`
- `normalized_rel_dir`
- `created_at`
- `tile_scale_m`
- `style_tags`
- `files`
- `upstream`

For `files`, the current normalized refs are:

- `base_color`
- `roughness`
- `normal`
- optional `ao`
- optional `displacement`
- `preview_image`

Each `files.*.path` value should be stored relative to `DATA_ROOT`.

## Source Metadata

Each normalized bundle should also write `source_metadata.json` with:

- selection identity
- source identity
- display metadata
- style tags
- tile scale
- normalized file names
- upstream raw source manifest relpath

## Current Helper Commands

Register one manually downloaded Poly Haven material:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  register-poly-haven-room-surface-material \
  polyhaven_wall_white_plaster_02_v0 \
  --selection sources/poly_haven/room_surface_selection_v0.json \
  --source-spec sources/poly_haven/source_spec_v0.json \
  --raw-material-dir /path/to/downloaded/material_dir
```

Normalize one registered Poly Haven material:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  normalize-poly-haven-room-surface-material \
  polyhaven_wall_white_plaster_02_v0 \
  --selection sources/poly_haven/room_surface_selection_v0.json \
  --source-spec sources/poly_haven/source_spec_v0.json
```
