# Asset Workflow v0

This note defines the first narrow workflow for `vgm-assets`.

## Goal

Bootstrap a protocol-aligned asset repo without waiting for real-source
ingestion to be complete.

The first deliverable is a toy living-room catalog that matches the categories
already expected by `vgm-scene-engine`.

## First Source Strategy

Use three source tiers in this order:

1. toy placeholders
2. curated open-source assets
3. Infinigen-derived assets

This keeps the repo useful immediately while leaving room for richer sources
later.

## First Catalog

The first committed catalog is:

- `catalogs/living_room_toy_v0/assets.json`

It covers these categories:

- `sofa`
- `coffee_table`
- `tv_stand`
- `bookshelf`
- `armchair`
- `side_table`
- `floor_lamp`

## Tooling

The current CLI now handles:

- validate an asset catalog against `vgm-protocol`
- generate an `AssetCatalogManifest`
- compute measurements from meshes
- register raw third-party source archives
- unpack registered zip sources into the processed data root
- organize the first Kenney selection into a normalized data layout

For the current Kenney living-room slice, the repo also exposes a single
wrapper script:

- `scripts/sources/rebuild_kenney_living_room_v0.sh`
- `scripts/catalogs/refresh_living_room_kenney_v0.sh`
- `scripts/pipelines/refresh_kenney_living_room_v0.sh`

It still does not yet:

- generate previews
- package materials
- derive full catalog metadata automatically from normalized source data
