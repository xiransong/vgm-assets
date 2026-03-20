# Support Clutter AI2-THOR v0

This note describes the first normalized AI2-THOR-derived prop slice for the
support-aware clutter bridge.

## Goal

Bootstrap the smallest practical prop slice for:
- `mug`
- `book`

using locally available AI2-THOR assets.

This slice is intended to support the first downstream bridge milestone:
- mugs on coffee tables and side tables
- books on coffee tables, side tables, and bookshelf shelves

## Source Selection

The current source-selection note is:

- `docs/architecture/support_clutter_prop_source_selection_v0.md`

The current selected source assets are:

### Mug

- `Mug_1`
- `Mug_2`
- `Mug_3`

### Book

- `Book_1`
- `Book_5`
- `Book_9`
- `Book_13`
- `Book_24`

## Current Materialized Data

Raw registered slice:

- `RAW_DATA_ROOT/sources/ai2thor/support_clutter_v0`

Processed normalized slice:

- `DATA_ROOT/assets/props/ai2thor/support_clutter_v0`

The processed slice currently contains:
- `3` mugs
- `5` books

Each normalized bundle currently includes:
- `model.fbx`
- `source_metadata.json`
- `bundle_manifest.json`
- `materials/` when available

## Current Catalog Artifacts

The current repo-side support-clutter artifacts live under:

- `catalogs/support_clutter_ai2thor_v0`

and include:

- `assets.json`
- `category_index.json`
- `support_compatibility.json`
- `asset_catalog_manifest.json`
- `measurements.json`
- `prop_annotations_v0.json`

The measurement report is derived from AI2-THOR Unity prefab colliders. For
the current slice, all selected props expose an explicit `BoundingBox`
collider, so the first measurements use that source-authored metadata rather
than ad hoc mesh parsing.

## Current Status

What exists already:
- source registration into `RAW_DATA_ROOT`
- normalized processed bundles in `DATA_ROOT`
- bundle manifests and source metadata
- approximate prop dimensions and footprints from prefab collider bounds
- first real prop placement annotations for the selected mugs and books
- first prop `AssetSpec` catalog for the selected slice
- first compact support-compatibility export for downstream support-aware placement

What still remains before the first frozen support-clutter export:
- a frozen snapshot export for `vgm-scene-engine`

## Refresh Command

The current prop metadata slice can be refreshed with:

```bash
./scripts/catalogs/refresh_ai2thor_support_clutter_metadata_v0.sh
```

This command:
- reads the processed AI2-THOR selection manifest from `DATA_ROOT`
- derives approximate prop measurements from raw prefab metadata in `RAW_DATA_ROOT`
- writes the current repo-side measurement and annotation artifacts
- validates the resulting prop annotation set

Refresh the full repo-side support-clutter catalog and compatibility slice:

```bash
./scripts/catalogs/refresh_support_clutter_ai2thor_v0.sh
```
