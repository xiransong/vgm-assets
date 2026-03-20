# Support Clutter Scene-engine Consumer v0

This note describes the first `vgm-assets -> vgm-scene-engine` handoff for
support-aware clutter.

## Frozen Snapshot

The first frozen snapshot is:

- `exports/scene_engine/support_clutter_v0_r1`

It contains:

- `prop_asset_catalog.json`
- `prop_category_index.json`
- `support_compatibility.json`
- `asset_catalog_manifest.json`
- `export_metadata.json`

The export-owned processed payload snapshot lives under:

- `DATA_ROOT/exports/scene_engine/support_clutter_v0_r1`

## What Scene-engine Should Read

`vgm-scene-engine` should:

1. use `prop_category_index.json` to sample prop assets by category
2. use `prop_asset_catalog.json` for the authoritative prop asset metadata
3. use `support_compatibility.json` to determine which prop categories are
   valid on which support surface types
4. resolve `files.*.path` against `VGM_ASSETS_DATA_ROOT`

## Expected Placement Flow

Recommended downstream flow:

1. place supporting furniture first
2. enumerate authored support surfaces on those assets
3. map support surface types through `support_compatibility.json`
4. sample a compatible prop category
5. sample a prop asset within that category
6. place the prop with support-surface margin checks and local collision checks

## Current Scope

The current `v0` support-clutter slice only covers:

- prop categories:
  - `mug`
  - `book`
- support surface types:
  - `coffee_table_top`
  - `side_table_top`
  - `bookshelf_shelf`

The current compatibility file is intentionally small and semantic. Scene-engine
should treat it as the source of truth for the first bridge rather than trying
to infer support compatibility from mesh geometry alone.
