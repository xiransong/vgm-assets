# Ceiling Light Fixtures v0 Plan

Status: `initial snapshot complete`
Last updated: `2026-03-17`

This note captures the next careful move for adding ceiling-light fixtures to
`vgm-assets`.

The immediate downstream target is the bridge already documented in
`vgm-scene-engine`:

- `/home/ubuntu/scratch/repos/vgm/vgm-scene-engine/docs/architecture/ceiling_light_fixtures_bridge_v0.md`

## Goal

Produce a small frozen ceiling-fixture snapshot that `vgm-scene-engine` can
place `1-3` times per room and use as anchors for default `ceiling` light
sources.

## What `vgm-assets` Should Own

- normalized ceiling-fixture payloads
- simple placement geometry
- preview packaging and provenance
- a frozen export snapshot with export-owned processed payloads

## What `vgm-assets` Should Not Do Yet

Not in this first step:

- lighting simulation
- photometric calibration
- ceiling fans as fixtures
- hanging or articulated fixture families
- `vgm-protocol` changes

## Current v0 Direction

Use exactly one source candidate for now:

- `lampSquareCeiling`

Do not include `ceilingFan`.

## Recommended v0 Record

Each ceiling-fixture record should minimally include:

- `fixture_id`
- `mount_type`
- `sample_weight`
- `dimensions`
- `footprint`
- `files`
- `provenance`

Recommended optional metadata:

- `display_name`
- `style_tags`
- `nominal_drop_height_m`
- `emission_hints`
- `source`
- `source_url`
- `license`

## Recommended v0 Export

Repo-side export metadata:

```text
exports/scene_engine/ceiling_light_fixtures_v0_r1/
  ceiling_light_fixture_catalog.json
  fixture_index.json
  fixture_catalog_manifest.json
  export_metadata.json
```

Export-owned processed payload snapshot:

```text
DATA_ROOT/exports/scene_engine/ceiling_light_fixtures_v0_r1/
  fixtures/
    ceiling/
```

## Current Kenney Direction

The local Kenney pack contains:

- `lampSquareCeiling.glb`
- `lampSquareCeiling_NE.png`

Measured raw bounds:

- `lampSquareCeiling.glb`: `0.12 x 0.23 x 0.12`

That likely means we will need the same treatment as the furniture slice:

- keep raw measurements for debugging
- add a scene-scale normalization layer for the working catalog

## Implementation Sequence

1. freeze the local ceiling-fixture record and export shape
2. add a small Kenney source-selection note for `lampSquareCeiling`
3. normalize the first fixture bundle into `DATA_ROOT`
4. build the first working catalog and `fixture_index.json`
5. export `ceiling_light_fixtures_v0_r1` as a frozen scene-engine snapshot

## Current State

The first `v0` ceiling-light fixture path is now in place:

- source selection metadata is defined for `lampSquareCeiling`
- the normalized Kenney fixture bundle is organized in `DATA_ROOT`
- the working catalog and `fixture_index.json` exist in `catalogs/`
- the frozen scene-engine snapshot `ceiling_light_fixtures_v0_r1` is exported

## Next Step

Pause here and let `vgm-scene-engine` consume
`ceiling_light_fixtures_v0_r1` once before expanding the fixture pool.
