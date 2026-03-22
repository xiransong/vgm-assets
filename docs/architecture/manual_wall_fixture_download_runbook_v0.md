# Manual Wall Fixture Download Runbook v0

This runbook describes how to stage the first real `wall_fixtures_v0` pair
after the metadata shortlist.

## Current Shortlist

- `painting`
  - `Victorian Framed Painting - PBR Game Ready`
  - <https://sketchfab.com/3d-models/victorian-framed-painting-pbr-game-ready-b2895c1c3b42401a949deac049e0051d>
  - license shown on page: `CC Attribution`
- `clock`
  - `Wooden Wall Clock`
  - <https://sketchfab.com/3d-models/wooden-wall-clock-f35bfeecca9b415a95e1e7d728becad6>
  - license shown on page: `CC Attribution`

## Important Caveat

As of `2026-03-22`, Sketchfab exposes both models as free downloadable assets,
but the actual download API requires authentication.

So the practical path is:

1. open the model pages in a logged-in browser
2. download the asset payloads manually
3. extract or rename the needed files into the staged raw tree below

## Raw Staging Layout

Stage the files under `RAW_DATA_ROOT/sources/manual/wall_fixtures_v0/` as:

```text
painting/candidate_painting_01/model.glb
painting/candidate_painting_01/preview.png
clock/candidate_clock_01/model.glb
clock/candidate_clock_01/preview.png
```

If the download gives a different mesh extension or preview filename, rename it
to match this layout before running the organizer.

## Organize Into DATA_ROOT

Once the four staged files exist, run:

```bash
./scripts/sources/organize_manual_wall_fixtures_v0.sh
```

This writes normalized bundles under:

```text
DATA_ROOT/fixtures/wall/manual/wall_fixtures_v0/
```

## Build The Catalog

Then run:

```bash
./scripts/catalogs/refresh_wall_fixtures_v0.sh
```

This writes:

- `catalogs/wall_fixtures_v0/wall_fixture_catalog.json`
- `catalogs/wall_fixtures_v0/fixture_category_index.json`
- `catalogs/wall_fixtures_v0/fixture_catalog_manifest.json`

## Export The First Snapshot

Finally run:

```bash
./scripts/exports/export_wall_fixtures_v0_r1.sh
```

This writes the frozen scene-engine handoff under:

- `exports/scene_engine/wall_fixtures_v0_r1/`

and the export-owned payload snapshot under:

- `DATA_ROOT/exports/scene_engine/wall_fixtures_v0_r1/`

## Validation Checklist

Before promoting the snapshot, verify:

- the painting front face is oriented into the room
- the clock front face is oriented into the room
- dimensions still look plausible after import
- previews match the selected assets
- attribution requirements for `CC-BY 4.0` are recorded in downstream docs if needed
