# Maintained Asset Export Alignment v0 Plan

Status: `active plan`
Last updated: `2026-03-22`

This note captures the next focused work needed to keep `vgm-assets` healthy as
an upstream maintained producer in the stronger `vgm-protocol` operating model.

## Why This Plan Exists

Two things are now true at the same time:

- `vgm-protocol` has tightened the maintained contract surface and added a more
  explicit golden-chain validation posture
- `vgm-assets` still has a few export and tooling issues that can cause silent
  drift, stale snapshot contents, or avoidable operator friction

The goal here is not to redesign asset semantics.

The goal is to make the maintained `vgm-assets` handoff deliberate, reproducible,
and easy to verify.

## External Inputs

- `/home/ubuntu/scratch/repos/vgm/vgm-protocol/docs/communications/protocol_status_update_2026_03.md`
- `/home/ubuntu/scratch/repos/vgm/vgm-protocol/docs/communications/vgm_assets_alignment_note_2026_03.md`
- `docs/architecture/export_snapshots_v0.md`
- `docs/architecture/scene_engine_consumer_v0.md`
- `exports/scene_engine/living_room_kenney_v0_r3`
- `exports/scene_engine/living_room_kenney_v0_r5`

## Main Goal

Deliver a maintained asset-export path that:

- stays protocol-valid against the current shared schemas
- uses a deliberately chosen maintained anchor
- avoids stale or machine-specific export artifacts
- has repo-local checks that catch regressions before downstream repos do

## Current Gaps To Close

1. the maintained anchor now needs to stay deliberate and stable
   - `vgm-protocol` currently names `living_room_kenney_v0_r3` as the
     maintained anchor
   - `vgm-assets` docs have now been aligned to the same default
   - future promotion to `r4` or `r5` should happen explicitly, not incidentally

2. export reruns are not safe enough yet
   - rerunning the same `export_id` can leave stale processed payload files in
     `DATA_ROOT`
   - export helpers currently assume repo-relative output paths in ways that
     make them harder to reuse and verify

3. generated artifacts are not portable enough yet
   - category indexes and measurement reports currently bake in absolute local
     filesystem paths
   - that makes committed artifacts noisy and less reproducible across machines

4. measurement tooling is too brittle
   - runtime dependencies used by measurement paths are not fully declared in
     `pyproject.toml`
   - `measure-catalog` currently fails on catalogs that legitimately omit
     `files.mesh`

5. repo-local verification is too thin
   - `vgm-assets` currently has no automated test suite
   - the maintained export path should have positive checks for the expected
     catalog and snapshot behavior

## Recommended Sequence

### Phase 1: Decide and document the maintained anchor

Make one explicit choice:

- either keep `living_room_kenney_v0_r3` as the maintained protocol anchor for
  now
- or deliberately promote `living_room_kenney_v0_r5` and coordinate that change
  with `vgm-protocol` and downstream docs/checks

For this phase:

- document the maintained anchor in `vgm-assets`
- align `docs/architecture/scene_engine_consumer_v0.md`
- align any export notes that currently imply a different maintained default
- keep non-maintained snapshots clearly labeled as historical, exploratory, or
  downstream-local

### Phase 2: Fix export correctness first

Prioritize correctness over feature expansion.

Implementation goals:

- clear or replace existing processed snapshot payload roots before rewriting a
  reused `export_id`
- make export helpers work with arbitrary output paths, not only repo-relative
  ones
- keep exported manifest file refs stable and intentional after that change
- preserve current protocol-valid exported JSON shapes

Minimum regression checks for this phase:

- rerunning the same export id after removing assets leaves no stale payloads
- exporting to a temporary directory outside the repo succeeds
- exported catalogs and manifests still validate cleanly

### Phase 3: Make generated artifacts portable

Remove machine-specific absolute paths from repo-side generated artifacts where
they are not essential.

Primary targets:

- `category_index.json`
- measurement reports
- any other committed generated JSON that currently records host-local absolute
  repo or data paths

Preferred direction:

- store repo-relative paths for repo-owned artifacts
- store `DATA_ROOT`-relative paths for processed payload refs
- only keep absolute paths in transient runtime-only summaries when there is a
  strong debugging need

### Phase 4: Harden measurement and packaging

Make the measurement workflow usable in the normal repo install path.

Implementation goals:

- declare measurement/runtime dependencies in `pyproject.toml`
- keep repo env bootstrap and package metadata consistent
- change `measure-catalog` so it skips records without `files.mesh`, or split
  the behavior into an explicitly strict mode and a default skip mode
- make measurement reports explicit about skipped assets when skipping occurs

### Phase 5: Add maintained-path verification

Add a small but meaningful automated test layer around the maintained export
path.

Recommended first tests:

- export rerun does not leave stale payload files
- export works with an output directory outside the repo
- category index generation emits portable paths
- measurement command behavior on mesh-backed and meshless catalogs
- maintained export fixtures validate against shared protocol schemas

Keep the first suite narrow and deterministic.

## First Deliverables

- one explicit maintained-anchor decision note in `vgm-assets`
- corrected export helpers for rerun safety and output-path handling
- portable category-index and measurement artifacts
- aligned dependency declarations for measurement paths
- first repo-local tests covering maintained export behavior
- regenerated maintained export artifacts after the fixes land

## Exit Criteria

We can treat this plan as complete when all of the following are true:

- `vgm-assets` names one maintained asset export anchor unambiguously
- rerunning maintained exports is idempotent with respect to exported payload
  contents
- maintained export generation does not depend on repo-local absolute output
  paths
- committed generated artifacts no longer bake in host-specific absolute paths
  unless explicitly justified
- the maintained export path has automated checks in the repo
- downstream protocol checks pass against the chosen maintained anchor

## Non-Goals

For this plan, do not:

- redesign `AssetSpec`
- add task-layer success semantics to asset exports
- broaden the maintained asset family beyond what the current downstream stack
  needs
- block ongoing Objaverse, room-surface, opening, fixture, or support-clutter
  work unless it directly conflicts with maintained export correctness

## Suggested Work Split

If we want the fastest practical path, do the work in this order:

1. maintained-anchor decision and doc alignment
2. export correctness fixes
3. portable artifact cleanup
4. packaging and measurement fixes
5. tests and maintained export regeneration

## Development Log

- 2026-03-22: created this plan after the stronger `vgm-protocol` maintenance
  update and a deep `vgm-assets` review.
- 2026-03-22: aligned `vgm-assets` docs to treat
  `living_room_kenney_v0_r3` as the current maintained protocol-facing anchor,
  while keeping `r4` and `r5` documented as later local follow-up snapshots.
- 2026-03-22: captured the anchor-alignment question between protocol-maintained
  `living_room_kenney_v0_r3` and current `vgm-assets` consumer guidance toward
  `living_room_kenney_v0_r5`.
