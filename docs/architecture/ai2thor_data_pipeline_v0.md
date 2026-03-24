# AI2-THOR Data Pipeline v0

This note defines the first AI2-THOR-specific storage and lifecycle contract
for `vgm-assets`.

It narrows the general rules in:

- `docs/architecture/storage_layout_v0.md`
- `docs/architecture/asset_workflow_v0.md`

and applies them to the full AI2-THOR staging and review path.

## Purpose

AI2-THOR is now used in two different but related ways inside `vgm-assets`:

- as a source of raw 3D object content
- as a source of semantic priors for object review

As the AI2-THOR scope expands from a tiny benchmark slice to a much larger
corpus, we need a filesystem contract that makes these layers easy to reason
about.

This note exists to answer:

- what is immutable raw AI2-THOR content?
- what processed AI2-THOR content is reproducible?
- where should review-state artifacts live?
- which repo-side artifacts are examples versus working copies?

## Core Principle

The AI2-THOR pipeline should always move through three distinct layers:

1. immutable raw staging
2. reproducible processed derivation
3. resumable human review

These layers should not be blurred together.

## Default Roots

The default roots remain:

- `RAW_DATA_ROOT=~/scratch/data/vgm/vgm-assets`
- `DATA_ROOT=~/scratch/processed/vgm/vgm-assets`

For AI2-THOR, the canonical source namespace is:

- `sources/ai2thor/`

## Layer 1: Immutable Raw Staging

All staged AI2-THOR source content must live under `RAW_DATA_ROOT`.

Canonical layout:

```text
RAW_DATA_ROOT/
  sources/
    ai2thor/
      <slice_id>/
        <category>/
          <asset_id>/
            raw/
              source_manifest.json
              source_prefab.prefab
              source_model.fbx
              <copied material files when needed>
        selection_manifest.json
```

Examples:

- `sources/ai2thor/support_clutter_v0/...`
- future:
  - `sources/ai2thor/object_semantics_wave1_v0/...`
  - `sources/ai2thor/object_semantics_wave2_v0/...`

### Raw Staging Rules

Once a raw bundle is registered:

- do not edit files in place
- do not overwrite the recorded upstream commit silently
- do not mix staged raw content with derived measurements or review notes

Each raw bundle should preserve:

- upstream provenance
- copied source files needed for derivation
- checksums and file sizes
- source-relative origin inside the AI2-THOR repo

Raw bundles are the immutable evidence of what was staged.

## Layer 2: Reproducible Processed Derivation

All normalized or derived AI2-THOR content should live under `DATA_ROOT`.

This includes:

- normalized asset bundles
- review-ready mesh preparations
- derived measurements
- generated previews
- downstream exports

Canonical processed layout:

```text
DATA_ROOT/
  assets/
    props/
      ai2thor/
        <slice_id>/...
    furniture/
      ai2thor/
        <slice_id>/...
  review/
    object_semantics/
      ai2thor/
        <slice_id>/
          candidate_annotations_v0.json
          reviewed_annotations_v0.json
          review_queue_v0.json
          review_meshes/
          previews/
          measurements/
  exports/
    scene_engine/
      <export_id>/...
```

### Processed Derivation Rules

Processed AI2-THOR content is expected to be reproducible from:

- raw staged bundles in `RAW_DATA_ROOT`
- repo-side selection and schema files
- repo-side generation scripts

It is acceptable to regenerate processed content when:

- normalization logic changes
- canonical-bounds derivation changes
- review mesh preparation changes
- queue generation rules change

It is not acceptable to treat processed content as immutable source evidence.

## Layer 3: Resumable Review Workspace

AI2-THOR review-state artifacts should live under the processed review
workspace, not only in the git repo.

Recommended review workspace:

```text
DATA_ROOT/
  review/
    object_semantics/
      ai2thor/
        object_semantics_v0/
          candidate_annotations_v0.json
          reviewed_annotations_v0.json
          review_queue_v0.json
          review_meshes/
          previews/
```

This workspace is where the explorer and the review queue should eventually
read and write by default.

### Why Review State Belongs In `DATA_ROOT`

Large-scale review should not require:

- frequent repo dirtiness
- accidental commits of private in-progress review decisions
- mixing small versioned examples with large working copies

The repo should keep:

- schemas
- architecture notes
- small example artifacts
- milestone or frozen snapshots when we deliberately want them versioned

The processed review workspace should keep:

- current working queue state
- current working reviewed annotations
- cached review-time derived artifacts

## Repo-Side Versus Data-Root Artifacts

### Repo-Side Artifacts

Keep these in the repo:

- source specs and selection files
- local schemas
- code and CLI helpers
- architecture notes and plans
- small benchmark examples
- frozen milestone examples that are intentionally committed

### Data-Root Artifacts

Keep these under `RAW_DATA_ROOT` or `DATA_ROOT`:

- staged raw AI2-THOR bundles
- normalized AI2-THOR payloads
- review-ready processed meshes
- large review working copies
- generated previews and measurements
- session-by-session review queue state

## AI2-THOR Lifecycle

The intended lifecycle for one asset is:

1. select an AI2-THOR asset in a repo-side selection file
2. stage immutable raw content under `RAW_DATA_ROOT`
3. derive processed review-ready content under `DATA_ROOT`
4. generate candidate annotations and queue entries
5. review the asset in the explorer
6. update reviewed annotations and queue state
7. optionally promote reviewed assets into downstream exports

Each step should leave behind artifacts in the correct layer.

## What Can Be Regenerated

Expected regenerable artifacts:

- processed bundle manifests
- canonical-bounds measurements
- review mesh preparations
- generated previews
- candidate annotation artifacts
- queue artifacts

These should be treated as derived outputs.

## What Must Be Preserved

Expected preserved artifacts:

- raw staged source bundles
- source manifests
- upstream commit and path provenance
- explicit reviewer decisions once a review wave becomes a milestone

For review decisions, the working copy may live in `DATA_ROOT`, but milestone
states may later be copied into repo-side committed examples if needed.

## Current Baseline

Today, the repo already demonstrates this split well for the small
`support_clutter_v0` AI2-THOR path:

- immutable raw bundles under `RAW_DATA_ROOT/sources/ai2thor/support_clutter_v0`
- normalized derived bundles under
  `DATA_ROOT/assets/props/ai2thor/support_clutter_v0`

What is still transitional is the object-semantics path:

- benchmark queue and annotation artifacts currently live in repo-side
  `catalogs/object_semantics_v0/`

That is acceptable for bootstrap, but it should not remain the only working
location once the AI2-THOR review corpus scales up.

## Decision

For AI2-THOR full-corpus staging and review:

- immutable staged source bundles live in `RAW_DATA_ROOT`
- normalized and review-ready derived assets live in `DATA_ROOT`
- active review-state artifacts should migrate toward a processed review
  workspace under `DATA_ROOT/review/...`
- repo-side `catalogs/` should hold examples and milestones, not the only live
  working copy

## Immediate Next Step

After this note, the next implementation step should be:

- create the processed AI2-THOR object-semantics review workspace layout and
  move the benchmark working artifacts toward it

That will make the current benchmark path match the intended long-term storage
contract.
