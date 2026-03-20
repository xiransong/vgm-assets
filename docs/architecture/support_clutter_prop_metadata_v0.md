# Support Clutter Prop Metadata v0

This note defines the first prop-side metadata contract for support-aware
clutter in `vgm-assets`.

The immediate downstream need is a very small first bridge:
- `mug`
- `book`

placed on:
- `coffee_table_top`
- `side_table_top`
- `bookshelf_shelf`

This note does not define a source pipeline yet. It freezes the minimum prop
metadata shape we want before we start normalizing actual prop assets.

## Why A Separate Prop Contract

The current `AssetSpec v0` schema is good for static assets, but it does not
express the placement-specific details that matter for support-aware clutter.

For example, scene-engine needs to know:
- which support surface types a prop may be placed on
- the effective support footprint of the prop base
- whether the prop needs to stay upright
- how much edge margin the prop needs on the parent support surface
- whether front-facing orientation matters

Those are not room-layout concerns. They belong with the prop asset metadata.

## Proposed Prop Placement Record

For the first `vgm-assets` clutter slice, each prop should carry:

- `asset_id`
- `category`
- `placement_class`
  - one of:
    - `mug`
    - `book`
    - `small_tabletop`
    - `decoration`
- `base_shape`
  - `rectangle` or `circle`
- `base_width_m`
- `base_depth_m`
- `support_margin_m`
  - minimum edge distance to preserve on the parent support surface
- `allowed_surface_types`
  - examples:
    - `coffee_table_top`
    - `side_table_top`
    - `bookshelf_shelf`
- `upright_axis`
  - axis that should align to the support normal
- `front_axis`
  - optional facing direction for asymmetric props
- `stable_support_required`
  - boolean
- `placement_style`
  - `scattered`, `aligned_front`, or `grid_like`
- `review_status`
  - `auto`, `reviewed`, or `uncertain`

## First Category Guidance

### Mug

Recommended initial defaults:
- `placement_class = mug`
- `base_shape = circle`
- `stable_support_required = true`
- `allowed_surface_types = [coffee_table_top, side_table_top]`
- `placement_style = scattered`
- `upright_axis = +y`

### Book

Recommended initial defaults:
- `placement_class = book`
- `base_shape = rectangle`
- `stable_support_required = true`
- `allowed_surface_types = [coffee_table_top, side_table_top, bookshelf_shelf]`
- `placement_style = grid_like` on shelves, `scattered` on tables
- `upright_axis = +y`

For `v0`, the prop-side metadata can stay coarse. The first success criterion
is not perfect clutter realism. It is a clean first end-to-end bridge.

## Relationship To Compatibility Export

This prop placement record and the support-compatibility export should agree,
but they do not need to be the same artifact.

Recommended direction:
- prop records carry local asset-level placement metadata
- a frozen `support_compatibility.json` export provides the compact downstream
  compatibility table used by scene-engine

## What Stays Out For Now

To keep the first bridge small, do not add yet:
- stackability
- contact-point polygons
- articulated book states
- open/closed variants
- simulator-style physics attributes

## Current Recommendation

Start with a local annotation-set schema for prop placement metadata. Once we
have a tiny real prop slice, we can decide what subset belongs in:
- the prop catalog itself
- the separate compatibility export
- any later protocol proposal
