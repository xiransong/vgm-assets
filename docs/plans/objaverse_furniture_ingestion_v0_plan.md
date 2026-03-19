# Objaverse Furniture Ingestion v0 Plan

Status: `active plan`
Last updated: `2026-03-19`

This note captures the first careful plan for scaling furniture diversity in
`vgm-assets` with Objaverse-family sources.

## Goal

Build a reproducible pipeline that can grow from a small curated Kenney living
room slice to a much larger, more realistic furniture pool.

The immediate goal is not bulk ingestion. The immediate goal is to make the
first Objaverse path safe and reviewable.

## Constraints

- keep `vgm-assets` as the only repo we change
- do not weaken the current frozen Kenney handoff
- keep license handling strict and explicit
- prefer rule-based, auditable filtering over black-box ranking in `v0`

## Phase 1

Freeze the source contract and review contract.

Deliverables:

- `sources/objaverse/source_spec_v0.json`
- `sources/objaverse/furniture_ingestion_policy_v0.json`
- `sources/objaverse/README.md`

## Phase 2

Build metadata-only intake.

Deliverables:

- metadata registration layout in `RAW_DATA_ROOT`
- processed candidate-table layout in `DATA_ROOT`
- first repo-side candidate manifest or review queue format

## Phase 3

Build narrowing filters before downloading large numbers of meshes.

Deliverables:

- license filter
- category keyword mapping
- negative keyword mapping
- geometry sanity checks after selective fetch

## Phase 4

Create the first accepted slice.

Deliverables:

- `20-40` accepted normalized furniture assets
- a working `living_room_objaverse_v0` catalog
- later a frozen `scene-engine` snapshot

## Initial Decision Rules

For the first Objaverse wave:

- allow only `CC0` and `CC-BY 4.0`
- stay inside the current living-room taxonomy
- keep Kenney as the stable fallback
- prefer assets with usable mesh payload and a practical preview path

## Current State

The initial planning layer is now in place:

- the repo-side Objaverse source spec is frozen
- the repo-side furniture ingestion policy is frozen
- the metadata-harvest contract is documented
- the first review-queue contract is documented
- lightweight validation commands now exist for both artifacts
- the narrowing contract from harvest to review queue is documented
- a stub harvest-to-review-queue helper seam now exists
- a mock harvest and first rule-based narrowing pass now exist

## Current State

The pipeline is now beyond mocks:

- raw metadata registration works for real artifacts
- metadata-harvest import works for real Objaverse metadata shards
- review-queue generation works on imported harvests
- a first-pass quality filter is in place
- the first official metadata shard has been reviewed manually
- the first accepted shortlist for selective geometry acquisition is now frozen

## Immediate Next Step

Do only this next:

- keep geometry acquisition selective, not bulk
- resolve the accepted shortlist into a geometry-acquisition manifest first
- fetch geometry only for the accepted shortlist from `000-014`
- record per-candidate acquisition outcome and payload availability
- inspect the first downloaded meshes before promoting any candidate into a
  normalized furniture bundle
