# Scene-Engine Consumer v0

This note defines the intended `vgm-scene-engine` handoff for the current
living-room asset snapshot.

## Maintained Anchor

The current maintained protocol-facing asset anchor is:

- `exports/scene_engine/living_room_kenney_v0_r3`

This is the snapshot that should be treated as the deliberate cross-repo default
until `vgm-protocol`, `vgm-assets`, and downstream consumers explicitly promote
a newer revision together.

## Snapshot To Consume

For the maintained path, `vgm-scene-engine` should consume the frozen snapshot:

- `exports/scene_engine/living_room_kenney_v0_r3`

It should not depend directly on the mutable working catalog under `catalogs/`.

Later snapshots remain available for local iteration:

- `living_room_kenney_v0_r4`
  - protocol-aligned support-surface follow-up
- `living_room_kenney_v0_r5`
  - expanded support-coverage follow-up

Those later snapshots should be treated as downstream-local or exploratory
revisions unless and until the maintained anchor is deliberately updated.

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

- `DATA_ROOT/exports/scene_engine/living_room_kenney_v0_r3/assets/...`
- `DATA_ROOT/exports/scene_engine/living_room_kenney_v0_r4/assets/...`
- `DATA_ROOT/exports/scene_engine/living_room_kenney_v0_r5/assets/...`

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

For the maintained `r3` snapshot:

- thin shared protocol support lives in:
  - `support.support_surfaces`
- the richer authored companion remains:
  - `support_surface_annotations_v1.json`

For later local follow-up snapshots such as `r5`:

- rich shared protocol support in `asset_catalog.json` is now carried under:
  - `support.support_surfaces_v1`
- thin compatibility support remains available under:
  - `support.support_surfaces`
- the richer support companion is:
  - `support_surface_annotations_v1.json`

This means scene-engine can use:

- `asset_catalog.json`
  - as the canonical shared support-surface contract for the chosen snapshot
- `support_surface_annotations_v1.json`
  - for local authored extras such as `supports_categories`,
    `placement_style`, `is_enclosed`, and review metadata
