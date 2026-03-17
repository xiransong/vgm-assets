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
- `catalogs/living_room_kenney_v0/size_normalization_v1.json`
- `catalogs/living_room_kenney_v0/category_index.json`
- `exports/scene_engine/living_room_kenney_v0_r1`
- `exports/scene_engine/living_room_kenney_v0_r2`
- `scripts/catalogs/normalize_living_room_kenney_v0.sh`
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

## Raw Measurement Note

The first mesh-bounds measurement pass now exists in:

- `catalogs/living_room_kenney_v0/measurements.json`

These values are raw mesh-bounds measurements from the Kenney GLBs. They remain
useful for debugging source geometry, but they are no longer the working
scene-scale dimensions for the catalog.

The current working axis interpretation for these Kenney GLBs is:

- `x -> width`
- `y -> height`
- `z -> depth`

## Size Normalization Revision

The current working catalog now applies a scene-scale normalization layer on top
of the raw Kenney mesh measurements.

The normalization plan is:

- `catalogs/living_room_kenney_v0/size_normalization_v1.json`

It pushes the current Kenney slice toward the same approximate room-scale
contract used by the original toy living-room assets in `vgm-scene-engine`,
while preserving candidate-level variation.

The current normalization revision updates all eight categories:

- `sofa`
- `coffee_table`
- `tv_stand`
- `bookcase`
- `bookshelf`
- `armchair`
- `side_table`
- `floor_lamp`

What is now measured:

- raw mesh `dimensions`
- raw mesh `footprint`
- raw support-surface geometry for table-like assets

What is now normalized in the working catalog:

- scene-scale `dimensions`
- scene-scale `footprint`
- scene-scale support-surface geometry
- provenance `config_id`

What still remains scaffolded:

- placement priors
- walkability priors
- affordance semantics

The current normalized geometry is intended to be consumed through:

- `exports/scene_engine/living_room_kenney_v0_r2`

## Current Semantics Review

The latest review applied three truth-preserving adjustments:

1. the small shelf asset was reclassified from `bookshelf` to `bookcase`
2. `coffee_table` spacing priors were relaxed to match the smaller measured mesh
3. `tv_stand` spacing priors were relaxed to match the measured mesh depth
