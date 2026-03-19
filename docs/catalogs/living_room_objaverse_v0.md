# living_room_objaverse_v0

This note tracks the first Objaverse-backed living-room furniture slice.

The purpose of this slice is not to replace the Kenney slice immediately.

The purpose is to prove that the `vgm-assets` pipeline can:

- selectively acquire real Objaverse geometry
- normalize it into reproducible furniture bundles
- promote those bundles into a working living-room catalog

## v0 Strategy

Start with the strongest three candidates from the first real shard:

- `Leather and Fabric Sofa`
- `table 70s`
- `nightstand`

Hold the other downloaded candidates until we inspect them more carefully.

## Current State

The first working catalog now exists at:

- `catalogs/living_room_objaverse_v0/assets.json`
- `catalogs/living_room_objaverse_v0/category_index.json`
- `catalogs/living_room_objaverse_v0/asset_catalog_manifest.json`

Current assets:

- `objaverse_leather_fabric_sofa_01`
- `objaverse_table_70s_01`
- `objaverse_nightstand_01`

Current categories:

- `sofa`
- `coffee_table`
- `side_table`

## Expected Role

This first slice should serve as:

- a realism-oriented supplement to the Kenney slice
- a test bed for Objaverse normalization and category priors
- the base for later `living_room_objaverse_v0_r1` snapshot export
