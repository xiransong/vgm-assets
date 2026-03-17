# Ceiling Light Fixtures Scene-Engine Consumer v0

This note defines the intended `vgm-scene-engine` handoff for the current
ceiling-light fixture snapshot.

## Snapshot To Consume

`vgm-scene-engine` should consume the frozen snapshot:

- `exports/scene_engine/ceiling_light_fixtures_v0_r1`

It should not depend directly on the mutable working catalog under
`catalogs/ceiling_light_fixtures_v0/`.

## Files To Read

- `fixture_index.json`
  - use for fixture lookup and uniform within-pool sampling
- `ceiling_light_fixture_catalog.json`
  - use for full fixture metadata and payload refs
- `fixture_catalog_manifest.json`
  - use for snapshot integrity and provenance checks
- `export_metadata.json`
  - use to identify the frozen exported revision

## File Ref Resolution

Payload refs in the exported catalog point to the export-owned processed payload
snapshot under:

- `DATA_ROOT/exports/scene_engine/ceiling_light_fixtures_v0_r1/fixtures/...`

They remain relative to `DATA_ROOT` in the JSON itself.

`vgm-scene-engine` should resolve them against:

- `VGM_ASSETS_DATA_ROOT`

## Minimal Consumer Rule

For `v0`, the expected downstream flow is:

1. load `fixture_index.json`
2. sample one fixture uniformly from the pool
3. load the chosen fixture from `ceiling_light_fixture_catalog.json`
4. resolve `files.*.path` against `VGM_ASSETS_DATA_ROOT`
5. attach it to the room ceiling as an architectural fixture, not as a furniture object
