# Source Policy v0

This note records the first asset-source policy for `vgm-assets`.

The goal is to keep the first real asset slice legally simple, operationally
lightweight, and compatible with the current living-room scene work.

## Recommendation

Use a staged source strategy:

1. toy placeholders first
2. curated open-source assets second
3. Infinigen-derived assets third

This means `vgm-assets v0` should not depend on Infinigen to become useful.

## Approved Now

### Kenney

Recommended use:
- first real mesh pool for furniture categories
- simple bootstrap assets that can replace abstract toy placeholders

Why:
- broad furniture coverage
- lightweight asset packs
- clear CC0 licensing
- low ingestion and redistribution risk

Current reference:
- <https://kenney.nl/assets/furniture-kit>

### Poly Haven

Recommended use:
- material library for normalized assets
- opportunistic source of CC0 geometry where relevant

Why:
- strong licensing clarity
- repo-friendly redistribution posture
- especially useful for materials and textures

Current references:
- <https://polyhaven.com/>
- <https://polyhaven.com/license>

## Allowed Later With Manual Review

### ShareTextures

Recommended use:
- selective materials and supporting texture sets

Why not default:
- licensing is generally permissive, but the site terms add redistribution and
  bulk-download constraints that are awkward for a repo-owned asset pipeline

Current references:
- <https://www.sharetextures.com/p/license>
- <https://www.sharetextures.com/p/terms>

### BlenderKit

Recommended use:
- manual discovery only

Why not default:
- mixed asset-specific licenses
- account/platform workflow overhead
- poor fit for a clean first-source policy

Current reference:
- <https://www.blenderkit.com/>

### Sketchfab

Recommended use:
- manual discovery only

Why not default:
- mixed licensing
- inconsistent download availability
- significant manual cleanup likely

Current reference:
- <https://sketchfab.com/licenses>

## Not Recommended For v0 Bootstrap

### Objaverse / Objaverse-XL

Recommended use:
- the first large-scale furniture-diversity source after the Kenney bootstrap

Why not as a naive bulk ingest:
- very large and heterogeneous
- object-level license handling is more complex
- geometry cleanup and metadata normalization cost is high

Current direction:
- proceed with a metadata-first ingestion plan
- use strict per-object license filtering
- keep the first wave inside the current living-room taxonomy

Current references:
- <https://huggingface.co/datasets/allenai/objaverse>
- <https://github.com/allenai/objaverse-xl>

### Infinigen

Recommended use:
- later source adapter prototype after the normalization pipeline is stable

Why not for `v0`:
- extracting reusable isolated assets is likely more work than curating a small
  open-source furniture pool
- material and provenance packaging need more design first

## Immediate Source Plan

For the next real asset milestone:

1. keep the existing toy living-room catalog as the stable fallback
2. add one small Kenney-backed furniture slice
3. add a Poly Haven material policy note
4. begin Objaverse planning before large-scale realistic furniture intake
5. defer Infinigen ingestion until the open-source path is working end to end

## Decision Rule

Only ingest a new source into `vgm-assets` when all of the following are true:

- the license is clear enough for the intended repo workflow
- provenance can be recorded per asset
- the asset can be normalized into `AssetSpec` cleanly
- the source does not force platform-coupled manual steps as the default path
