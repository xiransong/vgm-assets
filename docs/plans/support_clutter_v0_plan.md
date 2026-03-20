# Support Clutter v0 Plan

This note captures the next careful implementation steps for the first
support-aware clutter bridge.

## Goal

Deliver the smallest useful cross-repo handoff for:
- mugs on coffee tables and side tables
- books on coffee tables, side tables, and bookshelf shelves

## Immediate Inputs

- `docs/architecture/support_surface_semantics_v1.md`
- `catalogs/living_room_kenney_v0/support_surface_annotations_v1.json`
- `/home/ubuntu/scratch/repos/vgm/vgm-scene-engine/docs/architecture/support_clutter_bridge_v0.md`

## Recommended Sequence

1. define the local prop placement metadata contract
2. pick a tiny first prop source and a tiny first prop slice
3. normalize 2-3 mug assets and 3-5 book assets
4. write a small support-compatibility export
5. export the first frozen `support_clutter_v0_r1` snapshot

## First Deliverables

- local prop placement schema
- local prop placement validator
- small prop asset slice
- `support_compatibility.json`
- frozen scene-engine-facing support-clutter snapshot

## Non-Goals

For this phase, do not:
- redesign `vgm-protocol`
- add many clutter categories
- build a large automated clutter-ingestion system
- infer support geometry automatically from meshes

## Development Log

- 2026-03-20: defined the first local support-surface annotation set and the
  first Kenney furniture support-surface slice.
- 2026-03-20: started the prop-side metadata contract for `mug` and `book`.
- 2026-03-20: added the first local support-clutter prop annotation schema and
  validator command in `vgm-assets`.
