# Kenney Source Intake

This folder tracks the first open-source asset intake path for `vgm-assets`.
It stores repo-side metadata only, not the actual Kenney asset payloads.

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

The first organized Kenney-backed living-room slice currently covers fourteen
assets across these eight categories:

- `sofa`
- `coffee_table`
- `tv_stand`
- `bookcase`
- `bookshelf`
- `armchair`
- `side_table`
- `floor_lamp`

This mostly mirrors the current living-room categories already used in
`vgm-scene-engine`, with one important exception: the selected Kenney shelf
asset is small enough that we classify it as `bookcase`, not `bookshelf`.

It now includes second candidates for the major living-room furniture classes
and restores a large `bookshelf` category in addition to the smaller
`bookcase`.

The current organized subset is generated into:

- `DATA_ROOT/sources/kenney/furniture_kit/normalized/living_room_v0`

The next planned Kenney intake track is opening-bound assemblies:

- `sources/kenney/opening_selection_v0.json`
- `assemblies/kenney/opening_bundle_layout_v0.json`

The current starter candidates are:

- `wallDoorway`
- `wallWindow`

With likely later expansions:

- `wallDoorwayWide`
- `wallWindowSlide`

The first opening bundles are now organized under:

- `DATA_ROOT/assemblies/openings/kenney/opening_assemblies_v0`

You can rebuild the first `door` + `window` bundle pair with:

```bash
./scripts/sources/organize_kenney_openings_v0.sh
```

The next planned lighting-side Kenney intake track is ceiling fixtures:

- `sources/kenney/ceiling_fixture_selection_v0.json`
- `fixtures/kenney/ceiling_fixture_bundle_layout_v0.json`

The current starter candidate is:

- `lampSquareCeiling`

The first ceiling-fixture bundle is organized under:

- `DATA_ROOT/fixtures/ceiling/kenney/ceiling_light_fixtures_v0`

You can rebuild the first ceiling-fixture bundle with:

```bash
./scripts/sources/organize_kenney_ceiling_fixtures_v0.sh
```

The wall-fixture intake is currently expected to use a tiny manual shortlist
instead of a new Kenney slice:

- `sources/manual/wall_fixture_selection_v0.json`
- `fixtures/manual/wall_fixture_bundle_layout_v0.json`

## Intake Workflow

1. place the manually downloaded source zip into `RAW_DATA_ROOT` via
   `register-raw-source`
2. unpack the registered zip into `DATA_ROOT`
3. organize the selected asset subset into the normalized `living_room_v0`
   layout in `DATA_ROOT`
4. write protocol-facing `AssetSpec` records into a dedicated catalog
5. add preview images and material references when ready

The repo now also provides a single-command wrapper for this flow:

```bash
./scripts/sources/rebuild_kenney_living_room_v0.sh /path/to/kenney_furniture-kit.zip
```

## Notes

- Do not treat this folder as the final normalized asset package layout for all
  sources.
- This is only the first source-specific intake area.
- The repo-side source contract lives in `source_spec_v0.json`.
- The current selection list lives in `selection_v0.json`.
- The opening-assembly selection list lives in `opening_selection_v0.json`.
- The current selection list records normalized relative output directories in
  `DATA_ROOT`, but it is not itself a protocol `AssetSpec` catalog.
