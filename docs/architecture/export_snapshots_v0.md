# Export Snapshots v0

This note defines how `vgm-assets` hands stable catalog revisions to downstream
repos such as `vgm-scene-engine`.

## Rule

Downstream repos should not depend directly on mutable working catalogs under
`catalogs/`.

Instead, `vgm-assets` should publish frozen export snapshots under `exports/`.

Each snapshot should also own an immutable processed-payload snapshot under
`DATA_ROOT`, so downstream repos do not need to dereference the mutable working
processed tree.

Some snapshots may also carry companion metadata files when the current shared
protocol shape is intentionally thinner than the authored repo-local metadata.

## Scene-Engine Snapshot Layout

```text
exports/
  scene_engine/
    <export_id>/
      asset_catalog.json
      category_index.json
      asset_catalog_manifest.json
      export_metadata.json
      <optional companion metadata files>

DATA_ROOT/
  exports/
    scene_engine/
      <export_id>/
        assets/
          <category>/
            <asset_id>/
              ...
```

## Required Snapshot Files

- `asset_catalog.json`
- `category_index.json`
- `asset_catalog_manifest.json`
- `export_metadata.json`

## Metadata

`export_metadata.json` should record:

- `export_id`
- downstream consumer name
- source catalog id
- creation timestamp
- producer metadata
- checksummed file refs for the exported snapshot contents
- the `DATA_ROOT`-relative processed payload snapshot root
- checksummed payload refs for the exported asset files

## Current Snapshot

The first frozen scene-engine snapshot is:

- `exports/scene_engine/living_room_kenney_v0_r1`

The current size-normalized scene-engine snapshot is:

- `exports/scene_engine/living_room_kenney_v0_r2`

The current support-synced living-room snapshot is:

- `exports/scene_engine/living_room_kenney_v0_r3`

The current protocol-aligned support-surface living-room snapshot is:

- `exports/scene_engine/living_room_kenney_v0_r4`

The current expanded-support-coverage living-room snapshot is:

- `exports/scene_engine/living_room_kenney_v0_r5`

The first frozen room-surface material snapshot is:

- `exports/scene_engine/room_surface_materials_v0_r1`

The first frozen opening-assembly snapshot is:

- `exports/scene_engine/opening_assemblies_v0_r1`

The current downstream-consumer note is:

- `docs/architecture/scene_engine_consumer_v0.md`
- `docs/architecture/room_surface_scene_engine_consumer_v0.md`
- `docs/architecture/opening_assemblies_scene_engine_consumer_v0.md`

For the room-surface material snapshot, the frozen catalog contract is also
documented in:

- `docs/architecture/room_surface_material_consumer_guarantees_v0.md`
