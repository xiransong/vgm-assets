# AI2-THOR Full Staging And Review v0 Plan

Status: `active plan`
Last updated: `2026-03-24`

This note captures the careful next plan for scaling the AI2-THOR path from a
small benchmark slice to a full staged-and-reviewed corpus in `vgm-assets`.

## Goal

Stage all in-scope AI2-THOR objects into immutable raw bundles, derive
processed review-ready assets under `DATA_ROOT`, and review them session by
session with the existing explorer and batched review queue.

The goal is not one giant uninterrupted review pass.

The goal is to make full-corpus staging and batched review operational.

## Current Baseline

The current filesystem already shows the intended split:

- raw root:
  - `/home/ubuntu/scratch/data/vgm/vgm-assets`
- processed root:
  - `/home/ubuntu/scratch/processed/vgm/vgm-assets`

What is already working:

- AI2-THOR raw immutable bundles exist for `support_clutter_v0`
- processed AI2-THOR prop bundles exist under
  `assets/props/ai2thor/support_clutter_v0`
- object-semantics benchmark artifacts exist in repo-side `catalogs/`
- the `Object Semantics Explorer v0` is usable for real review
- the first AI2-THOR object-semantics review queue exists and is batched

What is not yet in place:

- full-corpus AI2-THOR raw staging
- a dedicated processed AI2-THOR object-semantics review workspace
- category-by-category queue generation for the broader corpus
- a documented end-to-end AI2-THOR staging pipeline beyond the benchmark slice

## Working Principles

- raw source content in `RAW_DATA_ROOT` is immutable once staged
- processed data in `DATA_ROOT` is reproducible and may be regenerated
- queue state and reviewed annotations are workflow artifacts, not raw source
- review should proceed in small batched sessions
- category-coherent review batches are preferred over random or giant batches
- repo-side `catalogs/` should hold small examples and versioned milestones, not
  the only working copy of large review-state artifacts

## Proposed AI2-THOR Layout

### Raw

Keep immutable AI2-THOR source bundles under:

- `RAW_DATA_ROOT/sources/ai2thor/<slice_id>/<category>/<asset_id>/raw/`

Each raw bundle should include:

- `source_manifest.json`
- `source_prefab.prefab`
- `source_model.fbx`
- copied source material files when needed

The raw manifest should remain the provenance anchor.

### Processed

Keep derived AI2-THOR assets and review artifacts under `DATA_ROOT`, split by
function:

- normalized assets:
  - `DATA_ROOT/assets/...`
- review workspace:
  - `DATA_ROOT/review/object_semantics/ai2thor/<slice_id>/...`
- downstream frozen exports:
  - `DATA_ROOT/exports/...`

Recommended first review workspace:

- `DATA_ROOT/review/object_semantics/ai2thor/object_semantics_v0/`

That workspace should eventually hold:

- `candidate_annotations_v0.json`
- `reviewed_annotations_v0.json`
- `review_queue_v0.json`
- review mesh payloads and previews if we choose to cache them there
- generated measurements and canonical-bounds side artifacts if needed

## Recommendation

Move in four narrow tracks, in this order:

1. formalize the AI2-THOR storage and pipeline contract
2. stage the full raw AI2-THOR intake wave into immutable bundles
3. derive processed review-ready assets and queue artifacts by category
4. review in short batched sessions with explicit pause/resume boundaries

## Phase 1: Freeze AI2-THOR Storage And Pipeline Contract

Write down the AI2-THOR-specific storage layout and lifecycle.

This should answer:

- what counts as immutable raw content?
- what processed artifacts are canonical versus disposable?
- where should working review-state files live?
- what repo-side artifacts should remain examples versus working copies?

Deliverables:

- one `ai2thor_data_pipeline_v0` architecture note
- one explicit directory convention for raw, processed, review, and export
- one short policy on what can be regenerated versus what must be preserved

Stop/go boundary:
- a teammate can stage one new AI2-THOR asset without guessing where files
  belong

## Phase 2: Stage Full Raw AI2-THOR Intake

Stage all in-scope AI2-THOR objects into immutable raw bundles under
`RAW_DATA_ROOT`.

This phase should be source-registration work only.

It should not depend on human review.

For each selected asset:

- copy the prefab into the raw bundle
- copy the model pack into the raw bundle
- copy material files when they are required for later review or packaging
- write `source_manifest.json`
- record source commit and source-relative origin

Deliverables:

- one AI2-THOR full-intake selection file
- one or more staging scripts to write raw bundles
- raw-bundle validation checks
- category counts and staging summary

Stop/go boundary:
- the full in-scope AI2-THOR wave exists as immutable content under
  `RAW_DATA_ROOT`

## Phase 3: Derive Processed Review-Ready Assets

Create processed review-ready assets from the immutable raw bundles.

This should include:

- canonical-bounds derivation
- normalized review mesh preparation
- bundle manifests
- source metadata copies
- preview generation where helpful

The processed review workspace should also receive:

- candidate object-semantics annotations
- reviewed annotation working copy
- batched review queue artifact

Deliverables:

- processed AI2-THOR review workspace under `DATA_ROOT/review/...`
- per-category or per-wave candidate annotation artifacts
- category-coherent review queue generation
- validation commands and tests for the generated artifacts

Stop/go boundary:
- any selected AI2-THOR asset can be opened in the explorer from processed
  review artifacts without ad hoc local preparation

## Phase 4: Run Batched Review Sessions

Use the explorer and review queue to review the corpus session by session.

Recommended session constraints:

- `20-40` assets or
- `30-45` minutes maximum

Recommended workflow:

1. open one queue batch
2. triage assets into:
   - `accepted`
   - `needs_fix`
   - `rejected`
   - `deferred` if the batch should pause
3. stop at the end of the batch or session target
4. return later to the next batch or the `needs_fix` subset

Deliverables:

- documented reviewer workflow
- queue-status update path
- one or more completed AI2-THOR review batches
- per-category review progress summary

Stop/go boundary:
- review can pause and resume across EC2 sessions without losing context or
  forcing repo-local cleanup

## Phase 5: Promote Reviewed Slices

Only after staging and review are stable should accepted AI2-THOR slices move
to frozen downstream exports.

Promotion rule:

- only assets that passed review for the current wave are eligible

Deliverables:

- reviewed-slice filtering path
- one reviewed AI2-THOR slice promoted downstream
- one lightweight consumer validation against the reviewed slice

Stop/go boundary:
- downstream consumers see only reviewed AI2-THOR assets, not raw candidates

## Suggested Review Waves

Do not start with the entire corpus at once.

Suggested waves:

1. supporting parents
- coffee tables
- side tables
- bookshelves
- TV stands

2. seating and large furniture
- chairs
- armchairs
- sofas
- benches

3. tabletop children
- mugs
- books
- bowls
- bottles
- decorations

4. long-tail household objects
- only after the queue and session workflow feels routine

## Immediate Next Moves

The next concrete tasks should be:

1. write `ai2thor_data_pipeline_v0.md`
2. move AI2-THOR object-semantics working artifacts toward a processed review
   workspace
3. define the full AI2-THOR selection scope for staging wave 1
4. build the raw-bundle staging script for that wave

## Success Criteria

We should consider this plan successful when:

- all in-scope AI2-THOR assets are staged immutably under `RAW_DATA_ROOT`
- processed review-ready assets exist under `DATA_ROOT`
- the review queue can be resumed across many short sessions
- the explorer operates on processed review artifacts, not ad hoc local files
- reviewed AI2-THOR subsets can be promoted downstream cleanly
