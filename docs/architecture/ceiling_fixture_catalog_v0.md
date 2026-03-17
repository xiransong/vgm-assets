# Ceiling Fixture Catalog v0

This note defines the internal `vgm-assets` shape for the first ceiling-light
fixture catalog.

It is intentionally repo-local for now. We are not changing `vgm-protocol`
yet.

The local validating schema for this frozen `v0` shape is:

- `schemas/local/ceiling_light_fixture_catalog_v0.schema.json`

## Scope

This first catalog covers ceiling-mounted light fixtures only.

It does not cover:

- free-standing lamps
- wall-mounted lights
- ceiling fans
- emitted-light simulation itself
- hanging chandeliers or rich drop-chain variants

## Why A Separate Track

Ceiling lights are not ordinary movable furniture assets.

They are:

- mounted to the ceiling plane
- sampled by ceiling-placement rules, not furniture-layout rules
- natural anchors for default `ceiling` light sources in the scene appearance layer

So the right abstraction is a ceiling-fixture catalog, not another furniture
category.

## Minimal Fixture Record

Each record should minimally contain:

- `fixture_id`
- `mount_type`
- `sample_weight`
- `dimensions`
- `footprint`
- `files`
- `provenance`

## `mount_type`

For `v0`, allowed values should be:

- `ceiling`

## Geometry

For `v0`, the fixture record should carry simple placement geometry:

- `dimensions`
  - `width`
  - `depth`
  - `height`
- `footprint`
  - `shape`
  - `width`
  - `depth`

This is enough for downstream ceiling-spacing logic without introducing a more
complex mounting model yet.

## `files` Coverage

For `v0`, the recommended payload refs are:

- `mesh`
- `preview_image`

Optional later additions:

- `collision_mesh`
- material payload linkage

Each `files.*.path` value should be stored relative to `DATA_ROOT`.

## Optional Metadata

The first catalog may also include:

- `display_name`
- `style_tags`
- `nominal_drop_height_m`
- `emission_hints`
  - `default_intensity_lm`
  - `default_color_temperature_k`
- `source`
- `source_url`
- `license`

These are useful, but they are not the minimum consumer contract.

## Sampling Policy

The initial policy should stay parallel to the existing catalogs:

- sample uniformly within the fixture pool
- keep `sample_weight = 1.0` for the first slice

## Supporting Index

The catalog should be paired with a compact `fixture_index.json`:

- `catalog_path`
- `fixture_count`
- `sampling_policy`
- `fixture_ids`

## Export Shape

The first downstream export should be:

```text
exports/scene_engine/ceiling_light_fixtures_v0_r1/
  ceiling_light_fixture_catalog.json
  fixture_index.json
  fixture_catalog_manifest.json
  export_metadata.json
```

And it should own an export-local processed payload snapshot under:

```text
DATA_ROOT/exports/scene_engine/ceiling_light_fixtures_v0_r1/
  fixtures/
    ceiling/
```

## v0 Candidate Direction

The current Kenney Furniture Kit appears to include one direct starter candidate:

- `lampSquareCeiling.glb`

The measured raw Kenney bounds are approximately:

- `lampSquareCeiling.glb`: `0.12 x 0.23 x 0.12`

That strongly suggests the same pattern we already saw with furniture and
opening assemblies:

- preserve raw measurements for debugging
- expect a scene-scale normalization layer before export
