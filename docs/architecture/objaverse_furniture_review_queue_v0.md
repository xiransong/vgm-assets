# Objaverse Furniture Review Queue v0

This note defines the first review-queue artifact for Objaverse furniture
ingestion in `vgm-assets`.

The review queue is the bridge between:

- automatic narrowing
- human curation
- normalized bundle creation

It is intentionally repo-local for now.

## Purpose

The first Objaverse wave should not move directly from metadata filtering to
bundle normalization.

Instead, narrowed candidates should enter a review queue that makes each
decision explicit and reproducible.

This gives us:

- auditable keep/reject decisions
- clean provenance from source metadata to accepted assets
- a stable place to attach notes before we normalize anything

## File Shape

The local validating schema for this queue is:

- `schemas/local/objaverse_furniture_review_queue_v0.schema.json`

Recommended repo-side artifact path:

- `sources/objaverse/review_queue_v0.json`

## Queue Structure

The queue is a JSON object with:

- `queue_id`
- `source_id`
- `policy_id`
- `created_at`
- `candidate_count`
- `candidates`

Each candidate is one narrowed Objaverse furniture object that passed the first
license and category filters.

## Required Candidate Fields

Each candidate should minimally include:

- `candidate_id`
- `object_uid`
- `source_url`
- `title`
- `license`
- `category_guess`
- `review_status`

## Recommended Candidate Fields

The first queue should also carry:

- `mesh_format`
- `has_preview`
- `preview_ref`
- `has_textures`
- `triangle_count`
- `bounds`
- `source_tags`
- `filter_trace`
- `review_notes`

This is enough for practical review without forcing full geometry
normalization.

## `review_status`

For `v0`, allowed values should be:

- `pending`
- `accepted`
- `rejected`
- `hold`

Meaning:

- `pending`
  - not reviewed yet
- `accepted`
  - approved to enter normalized bundle creation
- `rejected`
  - explicitly unsuitable for this wave
- `hold`
  - plausible later, but not part of the current accepted slice

## `filter_trace`

Each candidate should record a small machine-readable trace of why it reached
the queue.

Recommended fields:

- `license_rule`
- `category_rule`
- `format_rule`
- `notes`

This keeps the automatic narrowing auditable.

## Decision Rule

Only candidates with:

- `review_status = accepted`

should be eligible for normalized bundle creation in `DATA_ROOT`.

All others stay in the review queue only.

## Non-Goals For v0

This queue is not trying to be:

- a full dataset manifest
- a training dataset table
- a scene-engine contract
- a final normalized asset catalog

It is a curation artifact, nothing more.
