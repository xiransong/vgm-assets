# Wall Fixtures v0 Candidate Review

This note records the first metadata-level shortlist for the real
`wall_fixtures_v0` source pair.

Reviewed on `2026-03-22`.

## Scope

This is a metadata-only review.

We are not yet downloading or inspecting the real payload files, so the
decisions here are intentionally conservative.

## Current Accepted Pair

For the first real wall-fixture prototype, the current shortlist is:

- `painting`
  - `Victorian Framed Painting - PBR Game Ready`
  - source: Sketchfab
  - license on source page: `CC Attribution` / `CC-BY 4.0`
  - published: `2023-02-12`
- `clock`
  - `Wooden Wall Clock`
  - source: Sketchfab
  - license on source page: `CC Attribution` / `CC-BY 4.0`
  - published: `2024-05-25`

## Why These Two

The pair looks like a good first wall-fixture slice because:

- both are clearly wall-mounted decorative fixtures
- both have explicit public source pages and clear license labels
- neither appears to be a full-room scene or multi-object clutter bundle
- both are visually plausible for a living-room additive placement layer

## Conservative Caveat

These are only metadata-level accepts.

Before export, we still need to:

1. download the actual raw payloads
2. stage them under `RAW_DATA_ROOT/sources/manual/wall_fixtures_v0/`
3. inspect orientation, geometry cleanliness, and actual bounding size
4. update `raw_model_rel` and `raw_preview_rel` if the downloaded files differ
5. run the manual organizer and wall-fixture export pipeline

## Repo-side Artifacts

The current shortlist is recorded in:

- `sources/manual/wall_fixture_selection_v0.json`
- `sources/manual/wall_fixture_manual_review_v0.json`

The normalization scaffold is already prepared in:

- `fixtures/manual/wall_fixture_bundle_layout_v0.json`
- `scripts/sources/organize_manual_wall_fixtures_v0.sh`
