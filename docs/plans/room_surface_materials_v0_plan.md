# Room Surface Materials v0 Plan

Status: `active plan`
Last updated: `2026-03-17`

This note captures the next careful move for adding room-surface materials to
`vgm-assets` without expanding too fast.

The immediate downstream target is the bridge already documented in
`vgm-scene-engine`:

- `/home/ubuntu/scratch/repos/vgm/vgm-scene-engine/docs/architecture/room_surface_material_bridge_v0.md`

## Goal

Produce a small frozen room-surface material snapshot that `vgm-scene-engine`
can sample uniformly for:

- `floor`
- `wall`
- `ceiling`

This should stay parallel to the existing furniture-snapshot flow.

## What `vgm-assets` Should Own

- Poly Haven source registration and raw-file integrity checks
- normalized room-surface material bundles
- compact material metadata for scene-engine consumption
- a frozen export snapshot with export-owned processed payloads

## What `vgm-assets` Should Not Do Yet

Not in this first step:

- object-material normalization
- renderer-specific shader graphs
- style-conditioned material coherence
- lighting presets
- protocol changes in `vgm-protocol`

## Recommended v0 Material Record

Each material record should minimally include:

- `material_id`
- `surface_type`
- `sample_weight`
- `source`
- `display_name`
- `style_tags`
- `tile_scale_m`
- `files`
- `provenance`

For `files`, the expected `v0` payload refs are:

- `base_color`
- `roughness`
- `normal`
- optional `displacement`
- optional `ao`
- `preview_image`

All payload refs should be stored relative to `DATA_ROOT`.

## Recommended v0 Export

The room-surface export should mirror the current furniture snapshot pattern.

Repo-side export metadata:

```text
exports/scene_engine/room_surface_materials_v0_r1/
  room_surface_material_catalog.json
  surface_type_index.json
  material_catalog_manifest.json
  export_metadata.json
```

Export-owned processed payload snapshot:

```text
DATA_ROOT/exports/scene_engine/room_surface_materials_v0_r1/
  materials/
    floor/
    wall/
    ceiling/
```

## Recommended First Poly Haven Slice

Keep the first pool intentionally small:

- `floor`: 3 materials
- `wall`: 3 materials
- `ceiling`: 2 materials

The first slice should optimize for plausibility and easy debugging rather than
coverage.

## Implementation Sequence

1. define the internal room-surface material record shape in `vgm-assets`
2. add Poly Haven source docs, source spec, and a tiny curated selection list
3. implement raw-source registration and download planning for the selected
   Poly Haven materials
4. implement normalization into processed material bundles under `DATA_ROOT`
5. build the first working catalog and `surface_type_index.json`
6. export `room_surface_materials_v0_r1` as a frozen scene-engine snapshot

## Current Planning Baseline

The repo now has the first planning artifacts for this track:

- `sources/poly_haven/source_spec_v0.json`
- `sources/poly_haven/room_surface_selection_v0.json`
- `sources/poly_haven/room_surface_download_plan_v0.json`
- `materials/poly_haven/room_surface_bundle_layout_v0.json`
- `docs/architecture/room_surface_material_catalog_v0.md`
- `scripts/sources/plan_poly_haven_room_surface_v0.sh`

## Immediate Next Step

The next move should still avoid bulk implementation.

The single-material vertical slice now exists:

- raw `source_manifest.json` shape
- processed `bundle_manifest.json` shape
- first registration helper for one material
- first normalization helper for one material

It has been exercised locally with a dummy `white_plaster_02` material tree in
`/tmp`.

## Immediate Next Step

After this, the next practical step should be:

- implement one real Poly Haven API fetch path for one selected material
- connect that fetch step to the existing raw-source registration flow

Only after one real fetch works should we generalize to the full 8-material
room-surface slice.
