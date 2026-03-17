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

The current `v0` catalog is intentionally minimal:

- one `wall` material

Current material:

- `polyhaven_white_plaster_wall_02`

## Current Source Of Truth

The current catalog is generated from the normalized bundle:

- `DATA_ROOT/materials/room_surfaces/poly_haven/wall/polyhaven_white_plaster_wall_02/bundle_manifest.json`

## Next Expansion Rule

Expand this catalog only after each new material has completed the same flow:

1. live or manual source registration into `RAW_DATA_ROOT`
2. normalized bundle generation in `DATA_ROOT`
3. successful inclusion in the room-surface catalog

The next target additions should be:

- one `floor` material
- one `ceiling` material
