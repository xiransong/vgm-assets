# Living Room Kenney v0

This note describes the first real mesh-backed Kenney catalog in `vgm-assets`.

## Goal

Replace the pure toy-only asset slice with a first catalog whose payload
references point to real organized meshes and previews under the shared VGM
processed data root.

Catalog:

- `catalogs/living_room_kenney_v0/assets.json`
- `catalogs/living_room_kenney_v0/measurements.json`
- `scripts/catalogs/refresh_living_room_kenney_v0.sh`
- `scripts/pipelines/refresh_kenney_living_room_v0.sh`

## Current Scope

This first Kenney-backed catalog covers seven living-room categories:

- `sofa`
- `coffee_table`
- `tv_stand`
- `bookcase`
- `armchair`
- `side_table`
- `floor_lamp`

This no longer exactly matches the toy catalog because the selected Kenney shelf
asset is too small to call a large `bookshelf`, so it is classified here as
`bookcase`.

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

## Measured Geometry Revision

The current measured-geometry revision now updates all seven categories:

- `sofa`
- `coffee_table`
- `tv_stand`
- `bookcase`
- `armchair`
- `side_table`
- `floor_lamp`

What is now measured:

- `dimensions`
- `footprint`
- selected support-surface geometry for table-like assets

What still remains scaffolded:

- placement priors
- walkability priors
- affordance semantics

## Current Semantics Review

The latest review applied three truth-preserving adjustments:

1. the small shelf asset was reclassified from `bookshelf` to `bookcase`
2. `coffee_table` spacing priors were relaxed to match the smaller measured mesh
3. `tv_stand` spacing priors were relaxed to match the measured mesh depth
