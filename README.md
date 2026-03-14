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
- `docs/source_policy_v0.md`
- `sources/kenney/README.md`
- `docs/material_packaging_v0.md`

Current organized real-source subset:
- `/home/ubuntu/scratch/data/vgm/vgm-assets/sources/kenney/furniture_kit/normalized/living_room_v0`

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
- [ ] define the normalized internal asset record used before export
- [x] map internal records to protocol `AssetSpec`
- [x] export a first `AssetCatalogManifest`

### Milestone 3: First Living-Room Asset Slice

- [x] curate a minimal set of living-room categories used by
  `vgm-scene-engine`
- [x] define the first open-source source policy
- [~] support at least one Kenney-backed furniture slice
- [x] unpack and organize the Kenney Furniture Kit under the shared VGM asset
  data root
- [~] support Poly Haven materials for at least one normalized asset package
- [ ] support at least one Infinigen-derived asset path
- [x] compute dimensions, footprint, walkability, support surfaces, tags, and
  affordances
- [ ] generate preview images or equivalent inspection artifacts

### Milestone 4: Materials and Payload Packaging

- [ ] define how materials and textures are packaged for downstream use
- [ ] define canonical `FileRef` coverage for mesh, collision, preview, and
  material payloads
- [ ] document backend-agnostic versus backend-specific payload fields

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
  `/home/ubuntu/scratch/data/vgm/vgm-assets/sources/kenney/furniture_kit/normalized/living_room_v0`
- [x] selected first concrete Kenney candidates for all seven current
  living-room categories
