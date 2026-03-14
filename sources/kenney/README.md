# Kenney Source Intake

This folder tracks the first open-source asset intake path for `vgm-assets`.

## Source

- Source pack: Kenney Furniture Kit
- Source URL: <https://kenney.nl/assets/furniture-kit>
- License: CC0

## Why Kenney First

Kenney is the first real-source path because it is:
- furniture-focused
- license-simple
- lightweight to ingest
- easy to redistribute in a repo-centered workflow

This makes it a good bridge between the current toy catalog and a more realistic
asset pipeline.

## First Intake Scope

The first Kenney-backed slice is intentionally narrow:

- `sofa`
- `armchair`
- `side_table`

These categories map directly onto the current living-room scene needs and
cover both seating and support furniture.

## Intake Workflow

1. download the source pack manually and record the source version/date
2. identify candidate source files for the selected categories
3. copy raw source files under `sources/kenney/raw/`
4. normalize export layout under `sources/kenney/normalized/`
5. write protocol-facing `AssetSpec` records into a dedicated catalog
6. add preview images and material references when ready

## Notes

- Do not treat this folder as the final normalized asset package layout for all
  sources.
- This is only the first source-specific intake area.
- The current selection list lives in `selection_v0.json`.
