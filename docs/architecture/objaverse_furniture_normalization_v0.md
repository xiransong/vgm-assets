# Objaverse Furniture Normalization v0

This note defines the first normalization boundary for downloaded Objaverse
furniture in `vgm-assets`.

The immediate goal is not a large furniture library.

The immediate goal is to take a very small accepted raw-geometry slice and turn
it into normalized furniture bundles plus a working asset catalog.

## Scope

`v0` covers:

- raw Objaverse geometry already downloaded into `RAW_DATA_ROOT`
- a tiny normalization plan for a handful of accepted candidates
- normalized furniture bundles in `DATA_ROOT`
- a working `living_room_objaverse_v0` catalog in the repo

It does not cover:

- bulk normalization
- automated orientation repair
- collision-mesh generation
- category expansion beyond the current living-room taxonomy

## Normalization Inputs

The first normalization wave should start from:

- a selective geometry manifest
- a geometry inspection report
- a reference living-room furniture catalog for placement priors

For the first wave, the normalized reference source is:

- `catalogs/living_room_kenney_v0/assets.json`

## Normalization Plan

The normalization plan should freeze:

- candidate ids
- target `asset_id`s
- category assignment
- template asset for scene priors
- chosen uniform scale

The plan is intentionally explicit and human-reviewed. We are not trying to
infer all of this automatically in `v0`.

## Bundle Output

Each normalized furniture bundle should contain:

- `model.glb`
- optional `preview.*`
- `source_metadata.json`
- `bundle_manifest.json`

The bundle manifest should already carry the full asset-level contract needed to
promote the bundle into a protocol-valid `AssetSpec`.

## Promotion Rule

Only normalized bundles should feed the working Objaverse furniture catalog.

Raw downloaded geometry should never be handed directly to downstream repos.
