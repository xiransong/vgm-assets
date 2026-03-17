# Opening Assemblies v0 Plan

Status: `active plan`
Last updated: `2026-03-17`

This note captures the next careful move for adding concrete door and window
assemblies to `vgm-assets`.

The immediate downstream target is the bridge already documented in
`vgm-scene-engine`:

- `/home/ubuntu/scratch/repos/vgm/vgm-scene-engine/docs/architecture/opening_assemblies_bridge_v0.md`

## Goal

Produce a small frozen opening-assembly snapshot that `vgm-scene-engine` can
match against room `WallFeature`s for:

- `door`
- `window`

This should stay parallel to the existing furniture and room-surface-material
snapshot flows.

## What `vgm-assets` Should Own

- normalized opening-assembly payloads
- compatibility metadata for wall openings
- preview packaging and provenance
- a frozen export snapshot with export-owned processed payloads

## What `vgm-assets` Should Not Do Yet

Not in this first step:

- animated door state
- open/closed simulation
- procedural width/height retargeting
- curtains, shutters, blinds, or hardware variants
- `vgm-protocol` changes

## Recommended v0 Record

Each opening-assembly record should minimally include:

- `assembly_id`
- `opening_type`
- `sample_weight`
- `compatibility`
- `files`
- `provenance`

Recommended optional metadata:

- `display_name`
- `style_tags`
- `frame_depth_m`
- `door_swing`
- `glazing`
- `source`
- `source_url`
- `license`

## Recommended v0 Export

Repo-side export metadata:

```text
exports/scene_engine/opening_assemblies_v0_r1/
  opening_assembly_catalog.json
  opening_type_index.json
  assembly_catalog_manifest.json
  export_metadata.json
```

Export-owned processed payload snapshot:

```text
DATA_ROOT/exports/scene_engine/opening_assemblies_v0_r1/
  assemblies/
    door/
    window/
```

## Current Kenney Direction

The local Kenney pack appears to contain the first viable starter candidates:

- `wallDoorway.glb`
- `wallWindow.glb`

Possible later expansions:

- `wallDoorwayWide.glb`
- `wallWindowSlide.glb`

Measured raw bounds from the local pack:

- `wallDoorway.glb`: `1.00 x 1.29 x 0.089`
- `wallDoorwayWide.glb`: `1.00 x 1.29 x 0.089`
- `wallWindow.glb`: `1.00 x 1.29 x 0.089`
- `wallWindowSlide.glb`: `1.00 x 1.29 x 0.089`

That strongly suggests these assemblies will need the same treatment as the
furniture slice:

- preserve raw measurements for debugging
- add a scene-scale normalization layer for the working catalog

## Implementation Sequence

1. freeze the local opening-assembly record and export shape
  - done in:
    - `docs/architecture/opening_assembly_catalog_v0.md`
    - `schemas/local/opening_assembly_catalog_v0.schema.json`
2. add a small Kenney source-selection note for door/window candidates
3. normalize one door and one window payload into `DATA_ROOT`
4. build the first working catalog and `opening_type_index.json`
5. export `opening_assemblies_v0_r1` as a frozen scene-engine snapshot

## Immediate Next Step

The next move should still avoid broad expansion.

Do only this first:

- define the repo-side source-selection metadata for the first Kenney door and
  window candidates
- define the processed bundle layout for opening assemblies

Only after that should we build the first actual `door` and `window` bundles.
