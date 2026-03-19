# Objaverse Selective Geometry Acquisition v0

This note defines the first geometry-acquisition boundary for Objaverse
furniture in `vgm-assets`.

The goal is to move from metadata-only review to a very small geometry-backed
prototype without introducing bulk download behavior.

## Scope

This `v0` step is intentionally narrow.

It covers:

- one reviewed metadata shard
- one accepted shortlist from that shard
- selective geometry acquisition for only the accepted shortlist

It does not cover:

- bulk mesh download
- automatic acceptance of review-queue candidates
- normalization of all held candidates
- a production `living_room_objaverse_v0` catalog yet

## Why This Boundary Exists

The first real Objaverse shard already produced enough plausible furniture
candidates to test the next stage.

The right next move is not to fetch everything.

The right next move is to fetch only a small accepted slice so we can learn
about:

- payload availability
- format consistency
- geometry cleanliness
- texture completeness
- normalization cost by category

## Input Artifacts

Selective geometry acquisition starts from:

- a registered raw metadata artifact in `RAW_DATA_ROOT`
- an imported metadata-harvest artifact in `DATA_ROOT`
- a generated review queue in `DATA_ROOT`
- a repo-side manual review artifact with explicit `accepted` decisions

For the first prototype, the accepted shortlist is recorded in:

- `sources/objaverse/selective_geometry_objaverse_000_014_v0.json`

## Geometry Selection Artifact

The selection artifact should record:

- `selection_id`
- `source_id`
- `review_id`
- `queue_artifact`
- `selected_count`
- `selected_candidates`

Each selected candidate should record:

- `object_uid`
- `title`
- `category_guess`
- `expected_formats`
- `priority`
- `notes`

## Resolved Acquisition Manifest

Before any real mesh download, the accepted shortlist should be resolved into a
manifest that joins:

- the selective-geometry shortlist
- the imported metadata-harvest artifact

This manifest should record, per candidate:

- `source_url`
- `thumbnail_url` when available
- `available_formats`
- `preferred_download_order`
- canonical raw acquisition directory under `RAW_DATA_ROOT`

Important: this is still a planning and acquisition-boundary artifact. It does
not imply that direct download URLs are already known or stable.

## v0 Acquisition Rule

For `v0`, geometry acquisition should:

- operate only on `decision=accepted` candidates
- preserve candidate ordering by `priority`
- prefer `glb`, `gltf`, then `obj`
- record acquisition results per candidate
- stop short of automatic normalization if required payloads are missing

## Current Accepted Shortlist

The first accepted shortlist contains `5` candidates:

- `ac9ef69e1bbf4258aa489635b6cec609` `Earmes Lounge Chair`
- `c715fad78e6c4fc79b3b54d40ab50d07` `Leather and Fabric Sofa`
- `08d58a4f9c8e4a90b52cec383e05b662` `table 70s`
- `2daabc422a2e46f489f31c4a3b2b4d54` `Bookshelf`
- `415990b9b8d7434099682efbc9993132` `nightstand`

This is enough to test:

- category coverage across multiple living-room types
- category-specific normalization assumptions
- real geometry and texture handling

## Recommendation

The next geometry-backed prototype should fetch only this shortlist, then
inspect the actual payload quality before we accept more candidates from the
same shard or register another shard.
