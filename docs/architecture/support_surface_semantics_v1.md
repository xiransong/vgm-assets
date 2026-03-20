# Support Surface Semantics v1

This note defines the next richer support-surface contract that `vgm-assets`
should grow toward for object-on-surface placement.

The immediate motivation is downstream scene generation such as:
- place a desk in the room
- place cups, apples, books, or toys on that desk

The current `vgm-protocol` `AssetSpec` support block is a good `v0` seed, but
it is too thin for robust placement. Right now the shared `supportSurface`
shape is essentially:
- `surface_id`
- `height`
- `width`
- `depth`

That is enough for coarse "can hold objects" signaling, but not enough for:
- sampling stable object positions on a surface
- enforcing edge margins
- matching child object types to valid support types
- tracking object-local orientation
- distinguishing a tabletop from a shelf or a seat

This note does not change `vgm-protocol` yet. It freezes a `vgm-assets`
design target so we can move carefully before promoting any schema change.

## Why AI2-THOR Matters

AI2-THOR is a strong reference source for support semantics because it already
models:
- whether an object is a receptacle
- which object types can be placed in that receptacle
- whether an object is pickupable or moveable
- object mass and salient materials
- axis-aligned and object-oriented bounds

Relevant local references:
- `/home/ubuntu/scratch/repos/ai2thor/README.md`
- `/home/ubuntu/scratch/repos/ai2thor/ai2thor/tests/data/metadata-schema.json`
- `/home/ubuntu/scratch/repos/ai2thor/unity/Assets/DebugTextFiles/PlacementRestrictions.txt`
- `/home/ubuntu/scratch/repos/ai2thor/doc/static/ReleaseNotes/ReleaseNotes_1.0.md`
- `/home/ubuntu/scratch/repos/ai2thor/doc/static/ReleaseNotes/ReleaseNotes_3.0.md`

The key lesson is that placement is not just geometry. It is geometry plus
compatibility semantics.

## Core Concept

A support surface is an object-local support region on which another object may
be placed.

Examples:
- tabletop of a desk
- tabletop of a side table
- top surface of a TV stand
- shelf plane inside a bookcase
- countertop

This means the support-surface record needs to answer:
- where is the placeable region relative to the parent object?
- what is the shape and extent of that region?
- what direction is "up" for placement?
- how much safety margin should we keep from edges?
- what kinds of child objects are allowed there?

## Proposed Parent-Object Surface Record

For `vgm-assets`, the next richer surface record should carry:

- `surface_id`
  - stable object-local identifier such as `top`, `shelf_01`, `upper_shelf`
- `surface_type`
  - concrete exported label used by downstream consumers
  - examples:
    - `coffee_table_top`
    - `side_table_top`
    - `bookshelf_shelf`
- `surface_class`
  - smaller generic semantic class
  - one of:
    - `table_top`
    - `desk_top`
    - `side_table_top`
    - `tv_stand_top`
    - `bookshelf_shelf`
    - `shelf`
    - `counter_top`
    - `seat`
- `shape`
  - `rectangle` for `v1`
- `width_m`
- `depth_m`
- `height_m`
  - object-local support height from the object base frame
- `local_center_m`
  - `{x, y, z}` center of the placeable region in object-local coordinates
- `normal_axis`
  - usually `+y`
- `front_axis`
  - object-local front direction used for oriented placement
- `usable_margin_m`
  - edge buffer where we should not place child objects
- `supports_categories`
  - child object categories that are allowed on this surface
- `placement_style`
  - `scattered`, `centered`, `aligned_front`, or `grid_like`
- `is_enclosed`
  - useful later for cabinet shelves vs open shelves
- `review_status`
  - `auto`, `reviewed`, or `uncertain`

For `v1`, `shape=rectangle` is enough.

## Proposed Child-Object Placement Metadata

Support surfaces are only half of the contract. Child objects also need simple
placement metadata.

For tabletop-scale objects, `vgm-assets` should eventually carry:

- `placement_class`
  - `small_tabletop`
  - `book`
  - `food_item`
  - `toy`
  - `decoration`
- `base_shape`
  - `rectangle` or `circle`
- `base_width_m`
- `base_depth_m`
- `support_margin_m`
  - minimum distance from the support edge
- `allowed_surface_types`
  - compatible parent support types
- `upright_axis`
  - axis that should align to the support normal
- `front_axis`
  - optional facing direction for asymmetric objects
- `stable_support_required`
  - boolean

This child-side metadata does not need to go into `AssetSpec` immediately. It
is enough to freeze the design target so the next small-object track is not ad
hoc.

## Mapping From AI2-THOR

AI2-THOR field -> likely `vgm-assets` use

- `objectType`
  - category and tags
- `receptacle`
  - `support.supports_objects`
- `receptacleObjectIds`
  - scene-state occupancy signal, not asset-level support metadata
- `parentReceptacles`
  - scene relation, not asset-level metadata
- `pickupable`
  - child placement candidate prior
- `moveable`
  - large movable-object prior
- `mass`
  - stability and placement prior
- `salientMaterials`
  - tags and rough material priors
- `axisAlignedBoundingBox.size`
  - dimensions sanity check
- `objectOrientedBoundingBox.cornerPoints`
  - orientation QA and tighter support-region estimation

AI2-THOR `PlacementRestrictions.txt` is especially valuable as a reference
compatibility table. We should not copy it blindly, but it is a very good seed
for `supports_categories` and child-side `allowed_surface_types`.

## What We Should Mirror First

For the first `vgm-assets` upgrade, the minimum useful additions are:

1. richer parent support surfaces
- `surface_type`
- `surface_class`
- `local_center_m`
- `normal_axis`
- `front_axis`
- `usable_margin_m`
- `supports_categories`

2. a small shared support-surface vocabulary
- `table_top`
- `desk_top`
- `side_table_top`
- `tv_stand_top`
- `shelf`
- `counter_top`

3. a small child placement vocabulary
- `small_tabletop`
- `book`
- `food_item`
- `toy`
- `decoration`

That is enough to support the first realistic "object on surface" slice without
overbuilding.

## What Stays Out For Now

To keep this move careful, we should not add yet:
- arbitrary polygons for support regions
- multi-level stacking rules
- articulated support surfaces
- continuous physics stability scores
- simulator-specific occupancy state like `receptacleObjectIds`

Those are useful later, but they are not needed for the first tabletop clutter
pipeline.

## Suggested Rollout

1. keep `vgm-protocol` unchanged for the moment
2. add a local `vgm-assets` support-surface extension note or schema
3. annotate a few existing furniture assets by hand:
   - desk
   - coffee table
   - side table
   - TV stand
   - shelf/bookcase
4. define a tiny child-object placement record for cups/books/apples/toys
5. only then decide what subset should be promoted into `vgm-protocol`

## Current Recommendation

Use AI2-THOR as the semantic reference for support and placement concepts, but
do not try to mirror the entire simulator metadata model.

The right `vgm-assets` contract is:
- simpler than AI2-THOR
- richer than current `AssetSpec v0`
- explicitly oriented toward scene generation rather than runtime simulation
