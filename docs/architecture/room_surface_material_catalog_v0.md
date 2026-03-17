# Room Surface Material Catalog v0

This note defines the internal `vgm-assets` shape for the first room-surface
material catalog.

It is intentionally repo-local for now. We are not changing `vgm-protocol`
yet.

## Scope

This first catalog covers room-shell surface materials only:

- `floor`
- `wall`
- `ceiling`

It does not cover:

- object materials
- lighting presets
- renderer-specific shader parameters

## Minimal Material Record

Each record should minimally contain:

- `material_id`
- `surface_type`
- `sample_weight`
- `source`
- `display_name`
- `style_tags`
- `tile_scale_m`
- `files`
- `provenance`

## `files` Coverage

For `v0`, the recommended payload refs are:

- `base_color`
- `roughness`
- `normal`
- optional `displacement`
- optional `ao`
- `preview_image`

Each `files.*.path` value should be stored relative to `DATA_ROOT`.

## Sampling Policy

The initial policy should stay parallel to asset sampling:

- group by `surface_type`
- sample uniformly within a surface-type pool
- keep `sample_weight = 1.0` for the first slice

## Supporting Index

The catalog should be paired with a compact `surface_type_index.json`:

- `catalog_path`
- `surface_type_count`
- grouped surface pools with:
  - `sampling_policy`
  - `material_count`
  - `material_ids`

## Export Shape

The first downstream export should be:

```text
exports/scene_engine/room_surface_materials_v0_r1/
  room_surface_material_catalog.json
  surface_type_index.json
  material_catalog_manifest.json
  export_metadata.json
```

And it should have an export-owned processed payload snapshot under:

```text
DATA_ROOT/exports/scene_engine/room_surface_materials_v0_r1/
  materials/
    floor/
    wall/
    ceiling/
```

## First Implementation Rule

Before adding download or normalization logic, lock these first:

1. source spec
2. curated selection file
3. material record shape

That keeps the first Poly Haven ingestion small and reproducible.
