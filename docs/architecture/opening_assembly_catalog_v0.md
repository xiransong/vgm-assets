# Opening Assembly Catalog v0

This note defines the internal `vgm-assets` shape for the first opening
assembly catalog.

It is intentionally repo-local for now. We are not changing `vgm-protocol`
yet.

The local validating schema for this frozen `v0` shape is:

- `schemas/local/opening_assembly_catalog_v0.schema.json`

## Scope

This first catalog covers opening-bound architectural assemblies only:

- `door`
- `window`

It does not cover:

- movable furniture assets
- animated door state
- blinds, curtains, shutters, or hardware kits
- procedural resizing to arbitrary opening sizes

## Why A Separate Track

Door and window assemblies are not ordinary movable scene objects.

They are:

- attached to room-shell openings
- selected by compatibility with a `WallFeature`
- part of the architectural envelope rather than freestanding furniture

So the right abstraction is an opening-bound assembly catalog, not another
furniture category list.

## Minimal Assembly Record

Each record should minimally contain:

- `assembly_id`
- `opening_type`
- `sample_weight`
- `compatibility`
- `files`
- `provenance`

## `opening_type`

For `v0`, allowed values should be:

- `door`
- `window`

## `compatibility`

The compatibility block should stay fixed-size and simple for `v0`:

- `nominal_width_m`
- `nominal_height_m`
- `max_width_delta_m`
- `max_height_delta_m`

This lets `vgm-scene-engine` match an assembly to a room opening using opening
type plus width/height compatibility, without introducing procedural resizing.

## `files` Coverage

For `v0`, the recommended payload refs are:

- `mesh`
- `preview_image`

Optional later additions:

- `collision_mesh`
- material payload linkage

Each `files.*.path` value should be stored relative to `DATA_ROOT`.

## Optional Metadata

The first catalog may also include:

- `display_name`
- `style_tags`
- `frame_depth_m`
- `door_swing`
- `glazing`
- `source`
- `source_url`
- `license`

These are useful, but they are not the minimum consumer contract.

## Sampling Policy

The initial policy should stay parallel to the existing catalogs:

- group by `opening_type`
- sample uniformly within an opening-type pool
- keep `sample_weight = 1.0` for the first slice

## Supporting Index

The catalog should be paired with a compact `opening_type_index.json`:

- `catalog_path`
- `opening_type_count`
- grouped opening pools with:
  - `sampling_policy`
  - `assembly_count`
  - `assembly_ids`

## Export Shape

The first downstream export should be:

```text
exports/scene_engine/opening_assemblies_v0_r1/
  opening_assembly_catalog.json
  opening_type_index.json
  assembly_catalog_manifest.json
  export_metadata.json
```

And it should own an export-local processed payload snapshot under:

```text
DATA_ROOT/exports/scene_engine/opening_assemblies_v0_r1/
  assemblies/
    door/
    window/
```

## v0 Candidate Direction

The current Kenney Furniture Kit appears to include usable starter candidates:

- `wallDoorway.glb`
- `wallWindow.glb`

And likely later candidates:

- `wallDoorwayWide.glb`
- `wallWindowSlide.glb`

The current raw Kenney bounds measured from those GLBs are approximately:

- `wallDoorway.glb`: `1.00 x 1.29 x 0.089`
- `wallWindow.glb`: `1.00 x 1.29 x 0.089`

So, like the furniture slice, the raw geometry appears internally consistent but
undersized for a realistic room contract. The first implementation should
assume that opening assemblies may also require a scene-scale normalization
layer before export.
