# Opening Assemblies v0

This note tracks the first working opening-assembly catalog in `vgm-assets`.

## Goal

Create the first repo-side catalog artifact from real normalized opening
assembly bundles, starting with one Kenney door-side assembly and one Kenney
window-side assembly.

## Current Artifact Set

- `catalogs/opening_assemblies_v0/assemblies.json`
- `catalogs/opening_assemblies_v0/opening_type_index.json`
- `catalogs/opening_assemblies_v0/assembly_catalog_manifest.json`
- `scripts/catalogs/refresh_opening_assemblies_v0.sh`
- `exports/scene_engine/opening_assemblies_v0_r1`
- `scripts/exports/export_opening_assemblies_v0_r1.sh`

## Current Scope

The current `v0` catalog contains two opening-bound assemblies:

- `door`: 1
- `window`: 1

Current assembly ids:

- `kenney_wall_doorway_01`
- `kenney_wall_window_01`

## Current Source Of Truth

The current catalog is generated from these normalized bundles:

- `DATA_ROOT/assemblies/openings/kenney/opening_assemblies_v0/door/kenney_wall_doorway_01/bundle_manifest.json`
- `DATA_ROOT/assemblies/openings/kenney/opening_assemblies_v0/window/kenney_wall_window_01/bundle_manifest.json`

## Next Expansion Rule

Expand this catalog only after each new opening assembly has completed the same
flow:

1. source-selection metadata exists in the repo
2. normalized bundle generation succeeds in `DATA_ROOT`
3. successful inclusion in the opening-assembly catalog

The next likely additions should be:

- `kenney_wall_doorway_wide_01`
- `kenney_wall_window_slide_01`
