# Room Surface Material Consumer Guarantees v0

This note freezes the intended `v0` downstream contract for:

- `room_surface_material_catalog.json`

It applies to the frozen scene-engine export snapshot:

- `exports/scene_engine/room_surface_materials_v0_r1`

The local validating schema is:

- `schemas/local/room_surface_material_catalog_v0.schema.json`

## Stable Required Fields

Downstream consumers may rely on every material record containing:

- `material_id`
- `surface_type`
- `sample_weight`
- `files`
- `provenance`

For `files`, the `v0` export shape is keyed and stable. Consumers may rely on:

- `base_color`
- `roughness`
- `normal`
- `ao`
- `displacement`
- `preview_image`

Each file ref contains:

- `path`
- `format`
- `sha256`
- `size_bytes`

For `provenance`, consumers may rely on:

- `producer`
- `config_id`
- `upstream_ids`
- `upstream_bundle_relpath`

This provenance is material-catalog artifact provenance. It is not `SceneSpec`
or episode provenance from `vgm-protocol`.

## Optional Descriptive Fields

The current `v0` export may also include:

- `display_name`
- `style_tags`
- `tile_scale_m`
- `license`
- `source`
- `selection_id`
- `source_asset_id`
- `source_url`

These fields are useful and intended to remain available, but downstream repos
should treat them as optional metadata rather than the minimum contract.

## Consumer Behavior

For `vgm-scene-engine`, the intended behavior is:

1. sample uniformly within each `surface_type`
2. treat `files` as opaque material payload refs
3. resolve `files.*.path` against `VGM_ASSETS_DATA_ROOT`
4. use the descriptive fields only as optional hints
