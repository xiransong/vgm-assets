# AI2-THOR Object Semantics Scene-Engine Handoff v0

This note defines the current `vgm-assets -> vgm-scene-engine` handoff for the
reviewed AI2-THOR object-semantics slice.

## Current Reviewed Export

`vgm-scene-engine` should read the frozen reviewed slice:

- `exports/object_semantics/ai2thor_reviewed_object_semantics_v0_r3/`

The canonical reviewed artifact is:

- `exports/object_semantics/ai2thor_reviewed_object_semantics_v0_r3/reviewed_annotations_v0.json`

Role-specific filtered views are also available:

- `exports/object_semantics/ai2thor_reviewed_object_semantics_v0_r3/parent_object_annotations_v0.json`
- `exports/object_semantics/ai2thor_reviewed_object_semantics_v0_r3/child_object_annotations_v0.json`

## Categories Ready Now

The current `r3` slice includes reviewed AI2-THOR semantics for:

- `sofa`
- `coffee_table`
- `tv_stand`
- `floor_lamp`
- `armchair`
- `mug`
- `book`
- `bowl`

For the current living-room contract in
`vgm-scene-engine/contracts/living_room_scene_contract_v0.yaml`, this means the
newly reviewed AI2-THOR category coverage is now sufficient for:

- `sofa`
- `coffee_table`
- `tv_stand`
- `floor_lamp`
- `armchair`

The main remaining gap is:

- `side_table`

`bookshelf` also remains outside the reviewed slice for now.

## What Scene-Engine Can Trust

For each reviewed asset in `r3`, `vgm-scene-engine` may trust:

- `category`
- `front_axis`
- `up_axis`
- `bottom_support_plane`
- `support_surfaces_v1` when present
- `canonical bounds`

These fields have passed the current human review workflow and were promoted
only when both the reviewed annotation record and the review queue agreed on
`reviewed`.

## Current Limitation

This `r3` handoff is a reviewed semantics export, not yet a fully packaged
AI2-THOR geometry export.

So for `v0`, the intended usage is:

- use `r3` as the reviewed semantic source of truth for category-level
  scene-generation support
- keep geometry resolution and any temporary AI2-THOR mesh access on the
  existing local integration path until a later packaged-geometry bridge lands
