# Scene-Engine Consumer v0

This note defines the intended `vgm-scene-engine` handoff for the current
living-room asset snapshot.

## Snapshot To Consume

`vgm-scene-engine` should consume the frozen snapshot:

- `exports/scene_engine/living_room_kenney_v0_r1`

It should not depend directly on the mutable working catalog under `catalogs/`.

## Files To Read

- `category_index.json`
  - use for category-level lookup and uniform within-category sampling
- `asset_catalog.json`
  - use for full asset metadata and payload refs
- `asset_catalog_manifest.json`
  - use for snapshot integrity/provenance checks when needed
- `export_metadata.json`
  - use to identify the exported snapshot revision

## File Ref Resolution

Payload refs in the exported catalog remain relative to `DATA_ROOT`.

`vgm-scene-engine` should resolve them against:

- `VGM_ASSETS_DATA_ROOT`

If unset, the current `vgm-assets` default is:

- `~/scratch/processed/vgm/vgm-assets`

## Minimal Consumer Rule

For `v0`, the expected downstream flow is:

1. load `category_index.json`
2. choose a category and sample uniformly within that category
3. load the chosen asset from `asset_catalog.json`
4. resolve `files.*.path` against `VGM_ASSETS_DATA_ROOT`
