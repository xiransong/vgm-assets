# vgm-assets

Asset and material management repo for Vision-Grounded Motion.

This repo is the preprocessing, normalization, and export center for reusable
3D assets that will be consumed by `vgm-scene-engine` and downstream task and
vision pipelines.

## Repo Boundaries

This repo owns:
- raw asset-source adapters
- asset normalization and validation
- mesh and material packaging
- derived metadata for geometry, support, and affordances
- preview generation and file references
- export of protocol-compliant asset catalogs

This repo does not own:
- scene layout generation
- scene-level object placement
- task grounding logic
- motion-model training code

## Source Plan

Primary upstream sources:
- open-source assets
- Infinigen-generated assets from
  `/home/ubuntu/scratch/repos/hello-infinigen/third_party/infinigen`

The goal is to keep raw source handling source-specific, while exported asset
metadata and payload references remain protocol-shaped and source-agnostic.

Current sourcing recommendation:
- use toy assets first
- use curated open-source assets next
- prototype Infinigen only after the open-source path is stable

See:
- `docs/README.md`
- `docs/architecture/source_policy_v0.md`
- `docs/architecture/category_sampling_v0.md`
- `docs/architecture/export_snapshots_v0.md`
- `docs/architecture/scene_engine_consumer_v0.md`
- `docs/architecture/storage_layout_v0.md`
- `docs/architecture/room_surface_material_catalog_v0.md`
- `sources/kenney/README.md`
- `sources/poly_haven/README.md`
- `docs/architecture/material_packaging_v0.md`
- `docs/catalogs/living_room_kenney_v0.md`
- `docs/plans/room_surface_materials_v0_plan.md`

Current organized real-source subset:
- `DATA_ROOT/sources/kenney/furniture_kit/normalized/living_room_v0`

Default roots:
- `RAW_DATA_ROOT=~/scratch/data/vgm/vgm-assets`
- `DATA_ROOT=~/scratch/processed/vgm/vgm-assets`

Repo catalogs store payload file refs relative to `DATA_ROOT` so they remain
portable across machines with different local path layouts.

## Output Goals

This repo should eventually emit:
- normalized asset payloads
- previews and lightweight inspection artifacts
- protocol `AssetSpec` records
- protocol `AssetCatalogManifest` batches

## Planned Layout

Likely top-level areas:
- `docs/`: asset policy, naming, and provenance notes
- `materials/`: source-specific material intake and normalized bundles
- `sources/`: source-specific ingestion adapters
- `processors/`: normalization, measurement, and metadata extraction
- `catalogs/`: exported asset catalogs and manifests
- `tools/`: CLIs for ingest, validate, preview, and export
- `src/vgm_assets/`: Python helpers for protocol validation and manifest export

## Current Bootstrap Commands

Print the default data roots:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py print-paths --pretty
```

Register the manually downloaded Kenney source zip:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py register-raw-source \
  sources/kenney/source_spec_v0.json \
  --raw-file /path/to/kenney_furniture-kit.zip
```

Unpack the registered Kenney source zip into `DATA_ROOT`:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py unpack-registered-zip \
  sources/kenney/source_spec_v0.json
```

Organize the selected Kenney slice into the normalized data tree:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py organize-kenney-selection \
  sources/kenney/selection_v0.json \
  --source-spec sources/kenney/source_spec_v0.json
```

Rebuild the full Kenney `living_room_v0` slice in one command:

```bash
./scripts/sources/rebuild_kenney_living_room_v0.sh /path/to/kenney_furniture-kit.zip
```

If the raw source archive has already been registered in `RAW_DATA_ROOT`, the
same script can be rerun without the zip path:

```bash
./scripts/sources/rebuild_kenney_living_room_v0.sh
```

Refresh the Kenney catalog measurement report and manifest in one command:

```bash
./scripts/catalogs/refresh_living_room_kenney_v0.sh
```

Run the full Kenney `living_room_v0` refresh pipeline in one command:

```bash
./scripts/pipelines/refresh_kenney_living_room_v0.sh /path/to/kenney_furniture-kit.zip
```

If the raw archive is already registered in `RAW_DATA_ROOT`, rerun it without
the zip path:

```bash
./scripts/pipelines/refresh_kenney_living_room_v0.sh
```

Summarize category-level sampling candidates in a catalog:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py summarize-categories \
  catalogs/living_room_kenney_v0/assets.json \
  --pretty
```

Sample one asset uniformly within a category with a fixed seed:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py sample-category-asset \
  catalogs/living_room_kenney_v0/assets.json \
  sofa \
  --seed 7 \
  --pretty
```

Write a category-to-asset-id index for downstream consumers:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py write-category-index \
  catalogs/living_room_kenney_v0/assets.json \
  --output catalogs/living_room_kenney_v0/category_index.json
```

Export the first frozen scene-engine snapshot:

```bash
./scripts/exports/export_living_room_kenney_v0_r1.sh
```

This writes repo-side snapshot metadata under `exports/scene_engine/` and an
export-owned processed payload snapshot under `DATA_ROOT/exports/scene_engine/`.

Validate the first toy catalog:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py validate \
  catalogs/living_room_toy_v0/assets.json \
  --protocol-root ../vgm-protocol
```

Write the catalog manifest:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py write-manifest \
  catalogs/living_room_toy_v0/assets.json \
  --catalog-id living_room_toy_v0 \
  --output catalogs/living_room_toy_v0/asset_catalog_manifest.json \
  --protocol-root ../vgm-protocol
```

Validate the first Kenney-backed catalog:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py validate \
  catalogs/living_room_kenney_v0/assets.json \
  --protocol-root ../vgm-protocol
```

Measure mesh bounds for the Kenney-backed catalog:

```bash
PYTHONPATH=src python3 tools/measure_asset_catalog.py measure-catalog \
  catalogs/living_room_kenney_v0/assets.json \
  --output catalogs/living_room_kenney_v0/measurements.json \
  --pretty
```

## Environment

`vgm-assets` now has a lightweight micromamba setup under `env/` and
`scripts/env/`.

Create the env:

```bash
./scripts/env/create_env.sh vgm-assets
```

Verify the env:

```bash
./scripts/env/verify_env.sh vgm-assets
```

## Status Markers

- `[ ]` planned
- `[~]` in progress
- `[x]` finished

## Current Milestones

### Milestone 1: Repo Bootstrap

- [x] define repo layout and naming rules
- [x] write the first asset-ingestion workflow note
- [x] choose the first supported source adapters
- [x] add a validation CLI skeleton

### Milestone 2: Protocol-Aligned Asset Records

- [x] load and validate protocol `AssetSpec`
- [~] define the normalized internal asset record used before export
- [x] map internal records to protocol `AssetSpec`
- [x] export a first `AssetCatalogManifest`

### Milestone 3: First Living-Room Asset Slice

- [x] curate a minimal set of living-room categories used by
  `vgm-scene-engine`
- [x] define the first open-source source policy
- [~] support at least one Kenney-backed furniture slice
- [x] create the first real mesh-backed Kenney asset catalog
- [x] unpack and organize the Kenney Furniture Kit under the shared VGM
  processed data root
- [x] define a raw-data versus processed-data storage contract
- [x] add a lightweight dedicated micromamba env for `vgm-assets`
- [~] support Poly Haven materials for at least one normalized asset package
- [ ] support at least one Infinigen-derived asset path
- [x] compute dimensions, footprint, walkability, support surfaces, tags, and
  affordances
- [x] replace scaffolded toy geometry priors with mesh-derived measurements
- [ ] generate preview images or equivalent inspection artifacts

### Milestone 4: Materials and Payload Packaging

- [ ] define how materials and textures are packaged for downstream use
- [ ] define canonical `FileRef` coverage for mesh, collision, preview, and
  material payloads
- [ ] document backend-agnostic versus backend-specific payload fields
- [~] define the first room-surface material planning artifacts for Poly Haven

## Development Log

## 2026-03-14

- [x] created the first repo README as the working plan and progress tracker
- [x] set the repo direction as an asset and material management center rather
  than a scene-generation repo
- [x] locked the initial upstream-source plan to open assets plus Infinigen
  outputs
- [x] identified the first practical target as a protocol-aligned living-room
  asset slice for `vgm-scene-engine`
- [x] added the first repo layout, Python package skeleton, and protocol
  validation/export CLI
- [x] committed a toy living-room asset catalog covering the current seven
  scene-engine categories with per-asset provenance
- [x] added the first workflow note for the toy-first, open-source-next,
  Infinigen-later source strategy
- [x] added a first source policy note covering approved-now, later, and
  deferred asset sources for the repo
- [x] added the first Kenney intake scaffolding and a concrete three-category
  selection list for `sofa`, `armchair`, and `side_table`
- [x] added a first material-packaging note that keeps Poly Haven materials
  optional and backend-agnostic for `v0`
- [x] unpacked the Kenney Furniture Kit from
  `/home/ubuntu/scratch/transfer/kenney_furniture-kit.zip`
- [x] organized a first mesh-backed living-room subset under
  `DATA_ROOT/sources/kenney/furniture_kit/normalized/living_room_v0`
- [x] selected first concrete Kenney candidates for all seven current
  living-room categories
- [x] added `catalogs/living_room_kenney_v0/assets.json` with real mesh and
  preview refs backed by the organized Kenney subset
- [x] added a first mesh measurement CLI for catalog-backed asset meshes
- [x] applied the first measured-dimensions revision to the Kenney catalog for
  `sofa`, `armchair`, and `side_table`
- [x] completed the measured-geometry revision for all seven Kenney living-room
  categories
- [x] reclassified the small Kenney shelf asset as `bookcase` and relaxed
  toy-era spacing priors for `coffee_table` and `tv_stand`

## 2026-03-16

- [x] formalized `RAW_DATA_ROOT` and `DATA_ROOT` for `vgm-assets`
- [x] added a repo-side Kenney source spec with an expected raw archive hash
- [x] replaced absolute normalized data paths in the Kenney selection list with
  root-relative output directories
- [x] added CLI support to register a raw source archive, unpack a registered
  zip, and organize the selected Kenney normalized data slice
- [x] added a single-command entrypoint to rebuild the Kenney `living_room_v0`
  processed slice from repo metadata
- [x] added a single-command entrypoint to refresh the Kenney catalog
  measurement report and manifest
- [x] added a top-level single-command pipeline to refresh both the processed
  Kenney slice and the repo-side catalog artifacts
- [x] added a second Kenney sofa candidate to start testing within-category
  variation in the living-room slice
- [x] added a second Kenney coffee-table candidate to extend within-category
  variation beyond seating assets
- [x] expanded the living-room slice to 14 assets across 8 categories by
  filling the remaining single-candidate gaps and restoring a large
  `bookshelf` category
- [x] formalized `v0` category-level sampling as uniform within category and
  added small CLI helpers to inspect and reproduce it
- [x] added a generated category-to-asset index artifact for downstream
  consumers of the Kenney catalog
- [x] switched repo catalog file refs from absolute processed-data paths to
  `DATA_ROOT`-relative refs for better portability
- [x] added a frozen scene-engine snapshot export path for
  `living_room_kenney_v0_r1`

## 2026-03-17

- [x] extended the scene-engine export so `living_room_kenney_v0_r1` now owns
  an immutable processed payload snapshot under `DATA_ROOT/exports/`
- [x] reorganized `docs/` into `architecture/`, `catalogs/`, and `plans/`
  sections with a docs index
- [x] added an active room-surface-materials plan note aligned with the
  current `vgm-scene-engine` bridge design
- [x] added the first Poly Haven source-planning artifacts:
  - `sources/poly_haven/source_spec_v0.json`
  - `sources/poly_haven/room_surface_selection_v0.json`
  - `sources/poly_haven/README.md`
- [x] added the first room-surface material catalog-shape note for `vgm-assets`
