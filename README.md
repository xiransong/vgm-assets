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

## Output Goals

This repo should eventually emit:
- normalized asset payloads
- previews and lightweight inspection artifacts
- protocol `AssetSpec` records
- protocol `AssetCatalogManifest` batches

## Planned Layout

Likely top-level areas:
- `docs/`: asset policy, naming, and provenance notes
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
- [ ] support at least one open-source asset path
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
