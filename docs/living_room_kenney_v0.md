# Living Room Kenney v0

This note describes the first real mesh-backed Kenney catalog in `vgm-assets`.

## Goal

Replace the pure toy-only asset slice with a first catalog whose payload
references point to real organized meshes and previews under the shared VGM
processed data root.

In the repo catalog itself, those payload refs are stored relative to
`DATA_ROOT` rather than as machine-specific absolute paths.

Catalog:

- `catalogs/living_room_kenney_v0/assets.json`
- `catalogs/living_room_kenney_v0/measurements.json`
- `catalogs/living_room_kenney_v0/category_index.json`
- `exports/scene_engine/living_room_kenney_v0_r1`
- `scripts/catalogs/refresh_living_room_kenney_v0.sh`
- `scripts/pipelines/refresh_kenney_living_room_v0.sh`

## Current Scope

This first Kenney-backed catalog now covers fourteen assets across eight
living-room categories:

- `sofa`
- `coffee_table`
- `tv_stand`
- `bookcase`
- `bookshelf`
- `armchair`
- `side_table`
- `floor_lamp`

This no longer exactly matches the toy catalog because the selected Kenney shelf
asset is too small to call a large `bookshelf`, so it is classified here as
`bookcase`.

The current slice now includes:

- two `sofa` candidates
- two `coffee_table` candidates
- two `armchair` candidates
- two `side_table` candidates
- two `tv_stand` candidates
- two `floor_lamp` candidates
- one small `bookcase`
- one large `bookshelf`

Under the current `v0` sampling policy, those assets are sampled uniformly
within their category.

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

The current measured-geometry revision now updates all eight categories:

- `sofa`
- `coffee_table`
- `tv_stand`
- `bookcase`
- `bookshelf`
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
