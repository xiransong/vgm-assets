# Wall Fixtures v0 Plan

Status: `active plan`
Last updated: `2026-03-22`

This note captures the first `vgm-assets` work needed for the planned
`wall_fixtures_v0` additive scene layer in `vgm-scene-engine`.

The immediate downstream target is:

- `/home/ubuntu/scratch/repos/vgm/vgm-scene-engine/docs/architecture/wall_fixtures_bridge_v0.md`

## Goal

Produce a small frozen wall-fixture snapshot that `vgm-scene-engine` can use to
place a few wall-mounted decorative fixtures per room.

## What `vgm-assets` Should Own

- normalized wall-fixture payloads
- stable width / height / depth metadata
- simple wall-mount semantics
- preview packaging and provenance
- a frozen export snapshot with export-owned processed payloads

## What `vgm-assets` Should Not Do Yet

Not in this first step:

- lighting behavior
- articulated mounting hardware
- advanced wall-anchor geometry
- style-conditioned selection logic
- `vgm-protocol` changes

## Current v0 Direction

Keep the first slice intentionally tiny:

- `painting`
- `clock`

The immediate code path should be built now even if the first real source pair
lands in a later step.

## Recommended v0 Record

Each wall-fixture record should minimally include:

- `fixture_id`
- `category`
- `sample_weight`
- `dimensions`
- `mount`
- `files`
- `provenance`

Recommended optional metadata:

- `display_name`
- `style_tags`
- `preferred_height_band_m`
- `preferred_room_types`
- `review_status`
- `source`
- `source_url`
- `license`

## Recommended v0 Export

Repo-side export metadata:

```text
exports/scene_engine/wall_fixtures_v0_r1/
  wall_fixture_catalog.json
  fixture_category_index.json
  fixture_catalog_manifest.json
  export_metadata.json
```

Export-owned processed payload snapshot:

```text
DATA_ROOT/exports/scene_engine/wall_fixtures_v0_r1/
  wall_fixtures/
    painting/
    clock/
```

## Implementation Sequence

1. freeze the local wall-fixture record and export shape
2. add schema, Python helpers, CLI commands, and export support
3. add repo-local tests for catalog validation and export behavior
4. select a tiny first real source pair for `painting` and `clock`
5. build the first working catalog and `fixture_category_index.json`
6. export `wall_fixtures_v0_r1` as a frozen scene-engine snapshot

## Current State

The local wall-fixture architecture and code path are now in place.

The repo also now has a manual-shortlist source seam for the first real pair:

- `sources/manual/wall_fixture_source_spec_v0.json`
- `sources/manual/wall_fixture_selection_v0.json`
- `sources/manual/wall_fixture_manual_review_v0.json`
- `fixtures/manual/wall_fixture_bundle_layout_v0.json`
- `scripts/sources/organize_manual_wall_fixtures_v0.sh`

The first real `painting` / `clock` source pair is now shortlisted at the
metadata level, but its raw payloads are still not checked in.

## Next Step

Replace the placeholder manual shortlist entries with two reviewed real assets,
stage their raw files, and build the first real `wall_fixtures_v0_r1` snapshot
without redesigning the bridge.
