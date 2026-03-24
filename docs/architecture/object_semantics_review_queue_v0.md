# Object Semantics Review Queue v0

This note defines the first repo-local review queue for AI2-THOR object
semantics in `vgm-assets`.

The goal is to make review:

- batched
- resumable
- explicit about what is being reviewed
- separate from the annotation payload itself

## Purpose

The `Object Semantics Explorer v0` already lets a reviewer inspect one asset and
save decisions into reviewed annotation records.

That is necessary, but not sufficient for scaling review to hundreds or
thousands of assets.

We also need a queue artifact that tells us:

- which assets belong to the current review wave
- how assets are batched into review sessions
- which assets are still pending
- which assets are already reviewed, need fixes, or were rejected

This queue is workflow glue around the annotation artifacts.

It is not a second semantic source of truth.

## Current Focus

`v0` is intentionally scoped to AI2-THOR object-semantics review.

It does not try to solve:

- Objaverse curation
- downstream export manifests
- multi-reviewer conflict resolution
- full session analytics

## Review Contract

The queue makes the review target explicit.

The `review_scope_v0` list should match the same scope shown in the explorer:

- `asset_role`
- `category`
- `front_axis`
- `up_axis`
- `bottom_support_surface`
- `support_surfaces_v1`
- `canonical_bounds`

The queue does not redefine these fields.

It only records review workflow state around them.

## Queue Structure

The local schema is:

- `schemas/local/object_semantics_review_queue_v0.schema.json`

The first AI2-THOR queue artifact lives at:

- `catalogs/object_semantics_v0/ai2thor_review_queue_v0.json`

The queue is a JSON object with:

- `queue_id`
- `version`
- `source_id`
- `candidate_annotation_set_ref`
- `reviewed_annotation_set_ref`
- `created_at`
- `review_scope_v0`
- `item_count`
- `batch_count`
- `batches`

## Batch Structure

Each batch is one review session unit.

Required batch fields:

- `batch_id`
- `title`
- `status`
- `recommended_session_asset_count`
- `asset_count`
- `entries`

Recommended usage:

- keep batches category-coherent
- keep batches small enough for one short session
- let reviewers stop after one completed batch

## Entry Structure

Each entry minimally includes:

- `queue_item_id`
- `asset_id`
- `asset_role`
- `category`
- `sort_key`
- `priority`
- `queue_status`
- `annotation_review_status`

Optional workflow fields:

- `assigned_reviewer`
- `last_reviewed_at`
- `needs_fix_targets_v0`
- `review_notes`

## Status Semantics

`queue_status` is the queue-side workflow state:

- `pending`
  - not reviewed yet in this queue
- `in_progress`
  - currently being reviewed or partially reviewed
- `reviewed`
  - accepted in the current review wave
- `needs_fix`
  - the asset remains in scope but specific review targets need correction
- `rejected`
  - not accepted for the current wave
- `deferred`
  - intentionally postponed to a later review pass

`annotation_review_status` mirrors the current annotation-side status:

- `auto`
- `reviewed`
- `uncertain`
- `rejected`

This keeps the queue tied to the reviewed annotation artifact without copying
the whole record.

## Recommended AI2-THOR v0 Batching

Start with two tiny batches:

- `supporting_parents`
  - coffee table
  - side table
  - bookshelf
- `tabletop_children`
  - mug
  - book
  - bowl

This keeps review sessions short and conceptually coherent.

## Decision Rule

The queue should be used to drive work, not to replace annotation records.

The reviewed annotation artifact remains the field-level semantic source of
truth.

The queue is the source of truth for:

- what remains to be reviewed
- what batch an asset belongs to
- what order to tackle next
- whether the current pass accepted, rejected, or deferred the asset

## Non-Goals For v0

This queue is not trying to be:

- a general task system
- a final asset catalog
- a protocol artifact
- a complete multi-user review database

It is a lightweight, repo-local review workflow artifact.
