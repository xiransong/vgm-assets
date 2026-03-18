# Objaverse Furniture Ingestion v0

This note defines the first careful ingestion strategy for adding large-scale
furniture diversity to `vgm-assets` from Objaverse-family sources.

It is intentionally a planning and policy note first. We are not enabling bulk
Objaverse ingestion until the license, quality, and normalization rules are
frozen.

## Why Objaverse Next

Kenney gave us a clean `v0` bootstrap, but it is not enough for realistic
large-scale furniture diversity:

- the style is visibly stylized
- the number of useful living-room candidates is small
- within-category variation is still limited

Objaverse is attractive for the next phase because it offers scale that
curated small packs cannot:

- hundreds to thousands of potential furniture candidates
- broad long-tail object diversity
- strong potential for category expansion beyond the current living-room slice

## Why This Needs A Careful Plan

Objaverse should not be treated like Kenney.

The main risks are:

- mixed per-object licensing
- noisy category labels and metadata
- inconsistent geometry quality
- inconsistent texture/material quality
- duplicate or near-duplicate objects
- weak room-scale semantics unless we add our own normalization layer

So the correct approach is:

- metadata-first filtering
- strict license gating
- geometry sanity filtering
- manual review only after automatic narrowing
- frozen exports only after normalization

## Recommended Role In `vgm-assets`

Use Objaverse as a large-scale furniture diversity source, not as a direct
scene-engine input.

`vgm-assets` should own:

- metadata filtering and license filtering
- category mapping into our furniture taxonomy
- geometry and texture sanity checks
- candidate review artifacts
- normalized processed bundles
- frozen downstream snapshots

`vgm-scene-engine` should only consume the final frozen catalog snapshots.

## v0 Source Policy

For the first Objaverse ingestion wave, use a strict allowlist.

### Allow By Default

- `CC0`
- `CC-BY 4.0`

### Hold For Manual Legal Review

- `CC-BY-SA`
- `CC-BY 3.0`
- `CC-BY 2.x`

### Reject For v0

- `CC-BY-NC`
- `CC-BY-NC-SA`
- assets with unknown or missing license metadata

The goal is not maximum recall. The goal is a legally simple, reproducible
asset pool we can safely normalize and export.

## Recommended Furniture Scope

Start with the same living-room categories already exercised by
`vgm-scene-engine`:

- `sofa`
- `coffee_table`
- `tv_stand`
- `bookcase`
- `bookshelf`
- `armchair`
- `side_table`
- `floor_lamp`

Do not expand taxonomy and source scale at the same time.

## Ingestion Stages

### Stage 1. Metadata Harvest

Collect only source metadata and lightweight annotations first:

- object id / uid
- source URL
- title / name
- license
- available formats
- thumbnail / preview refs if available
- source tags / categories / descriptions

No object becomes a candidate until it passes metadata filtering.

The first local metadata-harvest contract is defined in:

- `docs/architecture/objaverse_furniture_metadata_harvest_v0.md`
- `schemas/local/objaverse_furniture_metadata_harvest_v0.schema.json`

### Stage 2. License Filter

Apply the strict license policy before any geometry processing.

This should output a repo-side candidate set that is already:

- license-allowed
- provenance-recorded
- reproducible from source metadata

### Stage 3. Category Mapping

Map source metadata into our local furniture taxonomy using a combination of:

- exact keyword rules
- synonym lists
- negative keyword filters
- optional embedding or classifier assistance later

For `v0`, start with transparent rule-based mapping only.

### Stage 4. Geometry Sanity Filters

Filter out candidates that are clearly poor fits:

- missing usable mesh payload
- empty or degenerate geometry
- extreme triangle counts
- extreme aspect ratios
- obviously broken bounds
- missing preview or impossible-to-preview assets when previewing is required

At this stage, the goal is still reduction, not perfect scoring.

### Stage 5. Review Queue

Generate a human-review queue for the narrowed candidates:

- category
- preview
- license
- source title
- quick geometry stats
- rejection reason or acceptance reason

Manual review should decide:

- keep
- reject
- keep-later

The first local review-queue contract is defined in:

- `docs/architecture/objaverse_furniture_review_queue_v0.md`
- `schemas/local/objaverse_furniture_review_queue_v0.schema.json`

### Stage 6. Normalized Bundle Build

Only accepted candidates get normalized into `DATA_ROOT`.

Each bundle should include:

- normalized mesh payload
- preview image
- source metadata
- bundle manifest

### Stage 7. Catalog Export

Accepted normalized bundles can then be turned into:

- a working catalog under `catalogs/`
- a frozen snapshot under `exports/scene_engine/`

## Recommended Quality Filters

For the first pass, use simple explicit filters:

- preferred formats:
  - `glb`
  - `gltf`
  - `obj`
- reject if no mesh file is available
- reject if bounds are zero or near-zero
- reject if the mesh is obviously extreme in one axis
- prefer textured assets over textureless assets
- prefer assets with a preview or one that can be rendered cheaply

Do not try to solve photorealism ranking perfectly in `v0`.

## Recommended Review Metrics

Each narrowed candidate should have at least:

- `license`
- `category_guess`
- `mesh_format`
- `triangle_count`
- `bounds`
- `has_textures`
- `preview_path`
- `review_status`
- `review_notes`

## Target Deliverables

The first Objaverse milestone should not be “thousands of furniture assets.”

It should be:

- a reproducible metadata filter
- a reproducible license policy
- a reproducible review queue
- one small accepted normalized furniture slice

If that works, scale becomes operational instead of aspirational.

## Suggested First Scale Target

Use a staged scale target:

1. metadata-only candidate pool across the eight living-room categories
2. review queue with `50-100` narrowed candidates
3. accepted normalized slice with `20-40` real furniture assets
4. later expand toward `200+`, then `1000+`

## Export Direction

Do not mutate the current Kenney snapshot.

Instead, create a new source-specific working catalog later, such as:

- `catalogs/living_room_objaverse_v0/`

And export source-frozen snapshots such as:

- `exports/scene_engine/living_room_objaverse_v0_r1/`

This keeps Kenney as the stable fallback while Objaverse matures.
