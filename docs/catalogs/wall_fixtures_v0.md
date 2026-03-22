# Wall Fixtures v0

This note tracks the first working wall-fixture catalog in `vgm-assets`.

## Goal

Create the first repo-side wall-fixture catalog artifact from normalized manual
fixture bundles, starting with one framed painting and one wall clock.

## Current Artifact Set

- `catalogs/wall_fixtures_v0/wall_fixture_catalog.json`
- `catalogs/wall_fixtures_v0/fixture_category_index.json`
- `catalogs/wall_fixtures_v0/fixture_catalog_manifest.json`
- `schemas/local/wall_fixture_catalog_v0.schema.json`
- `scripts/catalogs/refresh_wall_fixtures_v0.sh`
- `exports/scene_engine/wall_fixtures_v0_r1/`
- `scripts/exports/export_wall_fixtures_v0_r1.sh`

## Current Scope

The current `v0` catalog contains two wall-mounted decorative fixtures:

- `manual_painting_01`
- `manual_clock_01`

This is intentionally narrow. We are validating the wall-fixture handoff shape
before adding mirrors, televisions, shelves, or larger decorative sets.

## Current Source Of Truth

The current catalog is generated from:

- `DATA_ROOT/fixtures/wall/manual/wall_fixtures_v0/painting/manual_painting_01/bundle_manifest.json`
- `DATA_ROOT/fixtures/wall/manual/wall_fixtures_v0/clock/manual_clock_01/bundle_manifest.json`

## Current Measured Geometry

The working catalog carries measured dimensions from the staged GLB payloads:

- `manual_painting_01`
  - `width_m = 1.135768`
  - `height_m = 0.840015`
  - `depth_m = 0.047043`
- `manual_clock_01`
  - `width_m = 0.297541`
  - `height_m = 0.297541`
  - `depth_m = 0.036385`

## Current Snapshot

The first frozen scene-engine handoff is:

- `exports/scene_engine/wall_fixtures_v0_r1/`

Its export-owned payload snapshot lives under:

- `DATA_ROOT/exports/scene_engine/wall_fixtures_v0_r1/`

## Next Expansion Rule

Expand this catalog only after each new wall fixture has completed the same
flow:

1. source review and local raw staging
2. normalized bundle generation in `DATA_ROOT`
3. successful inclusion in the repo-side catalog
4. successful export into the frozen scene-engine snapshot
