# Opening Assemblies Scene-Engine Consumer v0

This note defines the intended `vgm-scene-engine` handoff for the current
opening-assembly snapshot.

## Snapshot To Consume

`vgm-scene-engine` should consume the frozen snapshot:

- `exports/scene_engine/opening_assemblies_v0_r1`

It should not depend directly on the mutable working catalog under
`catalogs/opening_assemblies_v0/`.

## Files To Read

- `opening_type_index.json`
  - use for opening-type lookup and uniform within-type sampling
- `opening_assembly_catalog.json`
  - use for full assembly metadata and payload refs
- `assembly_catalog_manifest.json`
  - use for snapshot integrity and provenance checks
- `export_metadata.json`
  - use to identify the frozen exported revision

## File Ref Resolution

Payload refs in the exported catalog point to the export-owned processed payload
snapshot under:

- `DATA_ROOT/exports/scene_engine/opening_assemblies_v0_r1/assemblies/...`

They remain relative to `DATA_ROOT` in the JSON itself.

`vgm-scene-engine` should resolve them against:

- `VGM_ASSETS_DATA_ROOT`

## Minimal Consumer Rule

For `v0`, the expected downstream flow is:

1. load `opening_type_index.json`
2. sample one compatible assembly within `door` or `window`
3. load the chosen assembly from `opening_assembly_catalog.json`
4. resolve `files.*.path` against `VGM_ASSETS_DATA_ROOT`
5. attach it to an existing room opening by `feature_id`, not as a movable object
