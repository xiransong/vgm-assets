# Object Semantics Reviewed Slice v0

This note defines the first frozen reviewed-only promotion path for
AI2-THOR object semantics in `vgm-assets`.

## Purpose

The AI2-THOR object-semantics pipeline now has:

- immutable raw staging
- processed candidate/reviewed annotations
- a batched review queue
- an EC2-hosted explorer

The next requirement is a strict downstream handoff seam.

Downstream consumers should not need to read:

- candidate annotations
- partially reviewed working copies
- queue entries that still say `pending` or `needs_fix`

They should read only a frozen slice that contains assets already accepted in
the current review wave.

## Promotion Rule

An AI2-THOR object may be promoted only when:

- the reviewed annotation record has `review_status=reviewed`
- the review queue entry has `queue_status=reviewed`

If these two sources disagree, promotion must fail.

This keeps:

- the reviewed annotation set as the field-level semantic source of truth
- the review queue as the workflow-state source of truth

and prevents accidental export of assets that are still in progress.

## Frozen Reviewed Slice Layout

The first frozen reviewed slice is written as a small repo-side export tree:

```text
exports/
  object_semantics/
    <export_id>/
      reviewed_annotations_v0.json
      parent_object_annotations_v0.json
      child_object_annotations_v0.json
      reviewed_slice_manifest.json
```

## Files

`reviewed_annotations_v0.json`

- all promoted reviewed assets for the current export

`parent_object_annotations_v0.json`

- only promoted `parent_object` assets

`child_object_annotations_v0.json`

- only promoted `child_object` assets

`reviewed_slice_manifest.json`

- export metadata
- source reviewed-annotation ref
- source review-queue ref
- counts by role
- category list

## Current Command

The promotion helper is:

- `promote-reviewed-object-semantics-slice`

The first convenience script is:

- `scripts/exports/export_ai2thor_reviewed_object_semantics_v0_r1.sh`

This command is intentionally strict by default:

- if no assets have been accepted yet, the export fails
- if a reviewed annotation and queue status disagree, the export fails

## Current Limitation

This promotion path freezes reviewed annotation artifacts only.

It does not yet package AI2-THOR normalized geometry for scene-engine
consumption.

That is intentional for `v0`.

The goal here is to establish a trustworthy reviewed-only semantic handoff
first, before broader downstream packaging expands.
