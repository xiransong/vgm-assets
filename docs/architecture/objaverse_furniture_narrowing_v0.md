# Objaverse Furniture Narrowing v0

This note defines the first narrowing contract from:

- metadata harvest

to:

- review queue

for Objaverse furniture ingestion in `vgm-assets`.

The goal is to make the transition from raw source metadata to human-reviewable
candidates explicit and auditable.

## Purpose

The narrowing stage is where we turn a broad source metadata table into a much
smaller review queue.

For `v0`, this stage should stay:

- rule-based
- deterministic
- transparent
- easy to inspect

We do not want opaque ranking or heuristic scoring to decide early acceptance.

## Inputs

The narrowing stage consumes:

- one metadata-harvest artifact
- one ingestion policy

Recommended inputs:

- `sources/objaverse/metadata_harvest_template_v0.json`
- `sources/objaverse/furniture_ingestion_policy_v0.json`

Later, generated harvest artifacts in `DATA_ROOT` should use the same schema.

## Output

The narrowing stage produces:

- one review queue artifact

Recommended output shape:

- `sources/objaverse/review_queue_template_v0.json`

or later a generated review queue artifact with the same schema.

## Narrowing Stages

### 1. License Gate

Apply the policy license allowlist and rejection list first.

Expected outcomes:

- allowed licenses continue
- rejected licenses are dropped immediately
- manual-review licenses may be included only if we explicitly choose that mode

For the current `v0` default, the narrowing path should only keep:

- `CC0`
- `CC-BY 4.0`

### 2. Minimal Metadata Gate

Reject records that do not have the minimum metadata needed for review:

- `object_uid`
- `source_url`
- `title`
- `license`

If these are missing, the record should not enter the review queue.

### 3. Category Guessing

Assign a provisional `category_guess` using the rule-based keyword mapping from
the ingestion policy.

The category guess should be derived from:

- `title`
- `source_tags`
- `source_categories`
- optionally `description`

For `v0`, use only transparent keyword and negative-keyword rules.

If no category is matched confidently, the record should not enter the queue.

### 4. Format Gate

If `available_formats` exists, prefer records with at least one supported mesh
format from policy:

- `glb`
- `gltf`
- `obj`

If format data is missing, the record may still enter the queue, but the trace
should say that the format gate was unresolved rather than passed.

### 5. Optional Preview Gate

If the policy prefers previewable assets, note whether the record has:

- `thumbnail_url`

This should not be a hard reject in `v0`, but it should be reflected in the
trace and candidate fields.

## Required Trace Fields

Each narrowed candidate must carry a `filter_trace` object with:

- `license_rule`
- `category_rule`
- `format_rule`
- `notes`

This is the minimum audit trail that explains why the candidate reached the
queue.

## Recommended Trace Conventions

Suggested string values:

- `license_rule`
  - `allowed_default`
  - `manual_review_allowed`
  - `rejected_license`
- `category_rule`
  - `keyword_match:<category>`
  - `no_match`
- `format_rule`
  - `preferred_format_present`
  - `preferred_format_missing`
  - `format_unknown`

These do not need to be the final exact strings, but they should stay stable
enough to be machine-readable and easy to review.

## Queue Defaults

When a record first enters the review queue:

- `review_status` should default to `pending`
- `review_notes` should default to empty or be omitted

Human review is what changes the status later.

## Determinism Rule

For the same:

- metadata harvest input
- ingestion policy
- narrowing configuration

the same records should produce the same review queue contents and trace.

This is important for reproducibility and debugging.

## Non-Goals For v0

The narrowing stage should not:

- download large geometry payloads by default
- compute final scene-scale dimensions
- make final keep/reject decisions
- attempt deep semantic classification

It is only the deterministic bridge from harvested metadata to reviewable
candidates.
