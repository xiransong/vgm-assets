# Support Surface Semantics v1 Plan

This note records the next careful plan for richer object-on-surface placement
metadata in `vgm-assets`.

## Context

We already have:
- furniture catalogs and frozen scene-engine exports
- room-surface materials
- opening assemblies
- ceiling-light fixtures

The next realism gap is small-object placement on supporting furniture.

Examples:
- cups on a desk
- books on a coffee table
- apples on a dining surface
- toys on a side table

## Goal

Freeze a practical support-surface semantics target before changing schemas or
adding new clutter-object sources.

## Immediate Inputs

- `/home/ubuntu/scratch/repos/vgm/vgm-protocol/schemas/core/asset_spec.schema.json`
- `/home/ubuntu/scratch/repos/ai2thor/ai2thor/tests/data/metadata-schema.json`
- `/home/ubuntu/scratch/repos/ai2thor/unity/Assets/DebugTextFiles/PlacementRestrictions.txt`
- `docs/architecture/support_surface_semantics_v1.md`

## Recommended Next Steps

1. add a local `vgm-assets` support-surface extension schema
2. annotate a tiny furniture slice with richer support-surface metadata:
   - one coffee table
   - one side table
   - one TV stand
   - one shelf-like asset
3. define a tiny child placement record for tabletop objects
4. test whether the metadata is expressive enough for downstream placement
5. only then consider a `vgm-protocol` proposal

## Non-Goals

For this phase, do not:
- redesign `vgm-protocol`
- add physics-heavy stability modeling
- add arbitrary polygon support regions
- add a large clutter-object source

## Milestone Boundary

We should consider this phase successful when we have:
- one written support-surface semantics note
- one local schema or schema-shaped contract for richer support records
- one tiny hand-annotated furniture subset using that richer contract

## Development Log

- 2026-03-20: wrote the first support-surface semantics note using AI2-THOR as
  the semantic reference for receptacle and placement concepts.
