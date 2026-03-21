# Scene-Engine Consumer v0

This note defines the intended `vgm-scene-engine` handoff for the current
living-room asset snapshot.

## Snapshot To Consume

`vgm-scene-engine` should consume the frozen snapshot:

- `exports/scene_engine/living_room_kenney_v0_r4`

It should not depend directly on the mutable working catalog under `catalogs/`.

## Files To Read

- `category_index.json`
  - use for category-level lookup and uniform within-category sampling
- `asset_catalog.json`
  - use for full asset metadata and payload refs
- `asset_catalog_manifest.json`
  - use for snapshot integrity/provenance checks when needed
- `support_surface_annotations_v1.json`
  - use for local support-surface authoring extras that are not yet part of the
    shared protocol shape
- `export_metadata.json`
  - use to identify the exported snapshot revision

## File Ref Resolution

Payload refs in the exported catalog point to the export-owned processed payload
snapshot under:

- `DATA_ROOT/exports/scene_engine/living_room_kenney_v0_r2/assets/...`
- `DATA_ROOT/exports/scene_engine/living_room_kenney_v0_r3/assets/...`
- `DATA_ROOT/exports/scene_engine/living_room_kenney_v0_r4/assets/...`

They remain relative to `DATA_ROOT` in the JSON itself.

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

## Support-aware Placement

For the current `r4` snapshot:

- rich shared protocol support in `asset_catalog.json` is now carried under:
  - `support.support_surfaces_v1`
- thin compatibility support remains available under:
  - `support.support_surfaces`
- the richer support companion is:
  - `support_surface_annotations_v1.json`

This means scene-engine can use:

- `asset_catalog.json`
  - as the canonical shared support-surface contract
- `support_surface_annotations_v1.json`
  - for local authored extras such as `supports_categories`,
    `placement_style`, `is_enclosed`, and review metadata
