# Living Room Kenney v0

This note describes the first real mesh-backed Kenney catalog in `vgm-assets`.

## Goal

Replace the pure toy-only asset slice with a first catalog whose payload
references point to real organized meshes and previews under the shared VGM
asset data root.

Catalog:

- `catalogs/living_room_kenney_v0/assets.json`
- `catalogs/living_room_kenney_v0/measurements.json`

## Current Scope

This first Kenney-backed catalog covers the same seven categories as the toy
catalog:

- `sofa`
- `coffee_table`
- `tv_stand`
- `bookshelf`
- `armchair`
- `side_table`
- `floor_lamp`

## Important Limitation

The current metadata is intentionally scaffolded:

- `dimensions`
- `footprint`
- placement priors
- walkability priors
- affordances and support metadata

These values are currently copied from the toy living-room catalog so that the
new Kenney slice can plug into the existing scene work immediately.

What is real already:

- `files.mesh`
- `files.preview_image`
- source identity and category mapping

## Next Upgrade

The next refinement pass should replace the scaffolded geometry priors with
mesh-derived measurements and review whether the toy placement/support priors
still make sense for each Kenney object.

## Current Measurement Note

The first mesh-bounds measurement pass now exists in:

- `catalogs/living_room_kenney_v0/measurements.json`

The measured mesh extents differ substantially from the current scaffolded toy
dimensions for several assets, which means the Kenney models and the toy priors
are not yet on the same scale contract.

The current working axis interpretation for these Kenney GLBs is:

- `x -> width`
- `y -> height`
- `z -> depth`

## First Measured Revision

The first measured-dimensions revision now updates:

- `sofa`
- `armchair`
- `side_table`

The remaining categories are still scaffolded from the toy catalog and should
be updated in later passes.
