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

## Important Current Limitation

This is a source-to-bundle slice, not a full prop catalog yet.

What exists already:
- source registration into `RAW_DATA_ROOT`
- normalized processed bundles in `DATA_ROOT`
- bundle manifests and source metadata

What still remains before the first frozen support-clutter export:
- prop dimensions and footprints
- prop placement annotations for the real selected assets
- a compact compatibility export
- a prop asset catalog and frozen snapshot

## Recommendation

The next clean step is to measure or otherwise normalize practical dimensions
for these props and then author the first real prop placement annotation set
for the selected AI2-THOR mugs and books.
