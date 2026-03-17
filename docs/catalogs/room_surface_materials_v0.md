# Room Surface Materials v0

This note tracks the first working room-surface material catalog in
`vgm-assets`.

## Goal

Create the first repo-side catalog artifact from real normalized
room-surface material bundles, starting with the first fetched Poly Haven wall
material.

## Current Artifact Set

- `catalogs/room_surface_materials_v0/materials.json`
- `catalogs/room_surface_materials_v0/surface_type_index.json`
- `catalogs/room_surface_materials_v0/material_catalog_manifest.json`
- `scripts/catalogs/refresh_room_surface_materials_v0.sh`

## Current Scope

The current `v0` catalog now contains six materials across the three target
surface types:

- `floor`: 2
- `wall`: 2
- `ceiling`: 2

Current materials:

- `polyhaven_wood_floor_01`
- `polyhaven_laminate_floor_02`
- `polyhaven_white_plaster_wall_02`
- `polyhaven_plaster_grey_wall_04`
- `polyhaven_white_plaster_ceiling_02`
- `polyhaven_plaster_grey_ceiling_04`

## Current Source Of Truth

The current catalog is generated from these normalized bundles:

- `DATA_ROOT/materials/room_surfaces/poly_haven/floor/polyhaven_wood_floor_01/bundle_manifest.json`
- `DATA_ROOT/materials/room_surfaces/poly_haven/floor/polyhaven_laminate_floor_02/bundle_manifest.json`
- `DATA_ROOT/materials/room_surfaces/poly_haven/wall/polyhaven_white_plaster_wall_02/bundle_manifest.json`
- `DATA_ROOT/materials/room_surfaces/poly_haven/wall/polyhaven_plaster_grey_wall_04/bundle_manifest.json`
- `DATA_ROOT/materials/room_surfaces/poly_haven/ceiling/polyhaven_white_plaster_ceiling_02/bundle_manifest.json`
- `DATA_ROOT/materials/room_surfaces/poly_haven/ceiling/polyhaven_plaster_grey_ceiling_04/bundle_manifest.json`

## Next Expansion Rule

Expand this catalog only after each new material has completed the same flow:

1. live or manual source registration into `RAW_DATA_ROOT`
2. normalized bundle generation in `DATA_ROOT`
3. successful inclusion in the room-surface catalog

The next target additions should be:

- a third `floor` material
- a third `wall` material
- a scene-engine-facing frozen export snapshot for this catalog
