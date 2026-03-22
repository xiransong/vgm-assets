# Manual Source Intake

This folder tracks tiny manually curated source slices that do not justify a
full dedicated source adapter yet.

The first use is `wall_fixtures_v0`, where we want exactly one reviewed
`painting` and one reviewed `clock`.

## Why A Manual Track

The wall-fixture `v0` slice is intentionally tiny and source-discovery-heavy.

That means the right first step is:

- manually shortlist a couple of candidates
- verify license and provenance per asset
- stage the raw files locally
- normalize them into the standard `vgm-assets` wall-fixture bundle layout

This avoids prematurely committing to a broad new source adapter.

## Current Files

- `wall_fixture_source_spec_v0.json`
- `wall_fixture_selection_v0.json`
- `wall_fixture_manual_review_v0.json`

## Raw Staging Layout

Stage the curated raw files under:

- `RAW_DATA_ROOT/sources/manual/wall_fixtures_v0/`

Each selected candidate should provide:

- one raw model file
- one preview image

The current selection file records their relative raw paths.

## Normalize Into DATA_ROOT

Once the raw files are staged, organize the normalized wall-fixture bundles
with:

```bash
./scripts/sources/organize_manual_wall_fixtures_v0.sh
```

That writes normalized bundles under:

- `DATA_ROOT/fixtures/wall/manual/wall_fixtures_v0/`

## Selection Rule

The first `wall_fixtures_v0` intake should stay extremely small:

- one `painting`
- one `clock`

Both should have:

- explicit `source_url`
- explicit reviewed license
- simple wall-mounted geometry
- generic living-room visual style

The current metadata-shortlisted pair is:

- `Victorian Framed Painting - PBR Game Ready`
- `Wooden Wall Clock`
