# Scene-Engine Consumer v0

This note defines the intended `vgm-scene-engine` handoff for the current
living-room asset snapshot.

## Snapshot To Consume

`vgm-scene-engine` should consume the frozen snapshot:

- `exports/scene_engine/living_room_kenney_v0_r3`

It should not depend directly on the mutable working catalog under `catalogs/`.

## Files To Read

- `category_index.json`
  - use for category-level lookup and uniform within-category sampling
- `asset_catalog.json`
  - use for full asset metadata and payload refs
- `asset_catalog_manifest.json`
  - use for snapshot integrity/provenance checks when needed
- `support_surface_annotations_v1.json`
  - use for richer authored support-surface metadata such as `surface_type`,
    `local_center_m`, and `usable_margin_m`
- `export_metadata.json`
  - use to identify the exported snapshot revision

## File Ref Resolution

Payload refs in the exported catalog point to the export-owned processed payload
snapshot under:

- `DATA_ROOT/exports/scene_engine/living_room_kenney_v0_r2/assets/...`
- `DATA_ROOT/exports/scene_engine/living_room_kenney_v0_r3/assets/...`

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

For the current `r3` snapshot:

- thin protocol support in `asset_catalog.json` is synced from the authored
  support annotations
- the richer support companion is:
  - `support_surface_annotations_v1.json`

This means scene-engine can use:

- `asset_catalog.json`
  - for the thin protocol-compatible support block
- `support_surface_annotations_v1.json`
  - for the richer support-surface semantics used by clutter placement
