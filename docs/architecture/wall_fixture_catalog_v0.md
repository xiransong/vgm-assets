# Wall Fixture Catalog v0

This note defines the internal `vgm-assets` shape for the first wall-mounted
fixture catalog.

It is intentionally repo-local for now. We are not changing `vgm-protocol`
yet.

The local validating schema for this frozen `v0` shape is:

- `schemas/local/wall_fixture_catalog_v0.schema.json`

## Scope

This first catalog covers small wall-mounted decorative fixtures only.

Initial `v0` scope:

- `painting`
- `clock`

It does not cover:

- sconces or emitted-light fixtures
- shelves
- mirrors
- televisions
- heavy framed art sets or gallery-wall groupings

## Why A Separate Track

Wall fixtures are not ordinary movable furniture assets.

They are:

- mounted to a wall plane
- constrained by corners and openings
- sampled as additive scene enrichments rather than primary layout anchors

So the right abstraction is a wall-fixture catalog, not another furniture
category.

## Minimal Fixture Record

Each record should minimally contain:

- `fixture_id`
- `category`
- `sample_weight`
- `dimensions`
- `mount`
- `files`
- `provenance`

## `category`

For `v0`, allowed values should be:

- `painting`
- `clock`

## Geometry

For `v0`, the wall-fixture record should carry simple placement geometry:

- `dimensions`
  - `width_m`
  - `height_m`
  - `depth_m`
- `mount`
  - `mount_type`
  - `mount_plane`
  - `usable_margin_m`

This is enough for downstream wall-span placement without introducing a more
complex mounting model yet.

Recommended `v0` mount values:

- `mount_type = wall_mounted`
- `mount_plane = vertical_wall`

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
- `preferred_height_band_m`
- `preferred_room_types`
- `review_status`
- `source`
- `source_url`
- `license`

These are useful, but they are not the minimum consumer contract.

## Sampling Policy

The initial policy should stay parallel to the existing fixture-style catalogs:

- sample uniformly within each fixture category
- keep `sample_weight = 1.0` for the first slice

## Supporting Index

The catalog should be paired with a compact `fixture_category_index.json`:

- `catalog_path`
- `category_count`
- `categories`
  - `sampling_policy`
  - `fixture_count`
  - `fixture_ids`

## Export Shape

The first downstream export should be:

```text
exports/scene_engine/wall_fixtures_v0_r1/
  wall_fixture_catalog.json
  fixture_category_index.json
  fixture_catalog_manifest.json
  export_metadata.json
```

And it should own an export-local processed payload snapshot under:

```text
DATA_ROOT/exports/scene_engine/wall_fixtures_v0_r1/
  wall_fixtures/
    painting/
    clock/
```

## v0 Candidate Direction

The best next source slice is a tiny pair of wall-mounted decorative fixtures:

- one `painting`
- one `clock`

It is better to start with a tiny stable pair than a broad decorative set.
