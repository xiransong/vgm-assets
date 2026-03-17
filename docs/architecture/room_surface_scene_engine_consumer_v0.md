# Room Surface Scene-Engine Consumer v0

This note defines the intended `vgm-scene-engine` handoff for the current
room-surface material snapshot.

## Snapshot To Consume

`vgm-scene-engine` should consume the frozen snapshot:

- `exports/scene_engine/room_surface_materials_v0_r1`

It should not depend directly on the mutable working catalog under
`catalogs/room_surface_materials_v0/`.

## Files To Read

- `surface_type_index.json`
  - use for surface-type lookup and uniform within-surface sampling
- `room_surface_material_catalog.json`
  - use for full material metadata and payload refs
  - contract details are frozen in `docs/architecture/room_surface_material_consumer_guarantees_v0.md`
- `material_catalog_manifest.json`
  - use for snapshot integrity and provenance checks
- `export_metadata.json`
  - use to identify the frozen exported revision

## File Ref Resolution

Payload refs in the exported catalog point to the export-owned processed payload
snapshot under:

- `DATA_ROOT/exports/scene_engine/room_surface_materials_v0_r1/materials/...`

They remain relative to `DATA_ROOT` in the JSON itself.

`vgm-scene-engine` should resolve them against:

- `VGM_ASSETS_DATA_ROOT`

## Minimal Consumer Rule

For `v0`, the expected downstream flow is:

1. load `surface_type_index.json`
2. sample one material uniformly within each of `floor`, `wall`, and `ceiling`
3. load the chosen materials from `room_surface_material_catalog.json`
4. resolve `files.*.path` against `VGM_ASSETS_DATA_ROOT`

Consumers should treat `files` as opaque payload refs and should not infer
extra semantics from filenames beyond the keyed file contract defined in:

- `docs/architecture/room_surface_material_consumer_guarantees_v0.md`
