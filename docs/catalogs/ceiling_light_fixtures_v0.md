# Ceiling Light Fixtures v0

This note tracks the first working ceiling-light fixture catalog in
`vgm-assets`.

## Goal

Create the first repo-side ceiling-fixture catalog artifact from normalized
Kenney fixture bundles, starting with a single flush-mount ceiling light.

## Current Artifact Set

- `catalogs/ceiling_light_fixtures_v0/fixtures.json`
- `catalogs/ceiling_light_fixtures_v0/fixture_index.json`
- `catalogs/ceiling_light_fixtures_v0/fixture_catalog_manifest.json`
- `schemas/local/ceiling_light_fixture_catalog_v0.schema.json`
- `scripts/catalogs/refresh_ceiling_light_fixtures_v0.sh`
- `exports/scene_engine/ceiling_light_fixtures_v0_r1`
- `scripts/exports/export_ceiling_light_fixtures_v0_r1.sh`

## Current Scope

The current `v0` catalog contains one ceiling-mounted fixture:

- `kenney_lamp_square_ceiling_01`

This is intentionally narrow. We are validating the ceiling-fixture handoff
shape before adding a second fixture.

## Current Source Of Truth

The current catalog is generated from:

- `DATA_ROOT/fixtures/ceiling/kenney/ceiling_light_fixtures_v0/kenney_lamp_square_ceiling_01/bundle_manifest.json`

## Current Scene-Scale Geometry

The working catalog carries a normalized ceiling-fixture contract:

- `width = 0.35`
- `depth = 0.35`
- `height = 0.12`

This is intentionally larger than the raw Kenney mesh bounds so that the
fixture reads plausibly at room scale.

## Next Expansion Rule

Expand this catalog only after each new fixture has completed the same flow:

1. source selection and normalized bundle generation in `DATA_ROOT`
2. successful inclusion in the repo-side catalog
3. successful export into the frozen scene-engine snapshot

The next likely addition would be a second simple ceiling fixture, but we are
deliberately pausing at one candidate for the first `v0` bridge.
