# Objaverse 000-014 Geometry Inspection v0

This note records the first raw-geometry inspection pass for the accepted
Objaverse shortlist from shard `000-014`.

Inputs:

- `sources/objaverse/selective_geometry_manifest_objaverse_000_014_v0.json`
- `RAW_DATA_ROOT/sources/objaverse/furniture_v0/geometry/...`
- `catalogs/living_room_kenney_v0/assets.json`

Method:

- load each downloaded raw mesh
- measure raw axis-aligned bounds
- compare sorted extents against the normalized Kenney category references
- estimate a best-fit uniform scale factor

Important:

- this is still a heuristic inspection pass
- it does not yet prove geometry quality or upright orientation
- it is meant to guide the first normalization prototype

## Early Takeaway

The five downloaded candidates are usable for the next step, but their raw
scales are not consistent.

The first inspection already suggests multiple unit regimes:

- `table 70s` looks close to a millimeter-scale asset
- `Earmes Lounge Chair` looks closer to a centimeter-scale asset
- `Leather and Fabric Sofa` appears to need a non-trivial arbitrary downscale

So the right next step is not direct catalog promotion.

The right next step is to freeze a small Objaverse normalization plan for these
five candidates and then build normalized bundles in `DATA_ROOT`.

## Current Inspection Read

Based on the first bounds-only inspection against the normalized Kenney living
room references:

- strongest immediate candidates:
  - `Leather and Fabric Sofa`
  - `table 70s`
  - `nightstand`
- likely hold for one more manual inspection pass:
  - `Earmes Lounge Chair`
  - `Bookshelf`

Why:

- `nightstand` fits the current side-table reference very closely after a
  modest downscale
- `Leather and Fabric Sofa` also lands in a plausible living-room range after a
  uniform downscale
- `table 70s` looks likely to be millimeter-scaled and otherwise plausible
- `Earmes Lounge Chair` and `Bookshelf` both need more care because their
  fitted extents still look less category-aligned than the other three
