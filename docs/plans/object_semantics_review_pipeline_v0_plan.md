# Object Semantics Review Pipeline v0 Plan

Status: `active plan`
Last updated: `2026-03-24`

This note captures the careful next plan for scaling object assets in
`vgm-assets` with reviewable semantics.

## Goal

Build a narrow, trustworthy pipeline for object semantics that can scale from a
tiny hand-reviewed slice to a much larger asset pool.

The immediate goal is not bulk asset ingestion.

The immediate goal is to make one end-to-end loop work:
- source asset
- auto-seeded candidate metadata
- human review
- frozen reviewed export

## Why This Needs A Dedicated Plan

The next asset-scale questions are tightly coupled:
- what metadata do we actually need for placement and interaction?
- what should AI2-THOR seed automatically?
- what must stay under human review?
- what kind of explorer and review queue can run well on EC2?

If we solve these separately, we risk creating:
- multiple incompatible metadata formats
- auto-generated fields that reviewers cannot realistically validate
- a review UI that does not match the stored artifacts
- downstream exports that are too early to trust

## Recommendation

Move in three narrow tracks, in this order:

1. freeze the metadata contract
2. build the AI2-THOR auto-seeding path
3. build the EC2-hosted review loop on top of the same artifacts

This keeps `vgm-assets` as the source of truth while making human review a
first-class part of the asset pipeline.

## Working Principles

- keep raw source data, candidate metadata, reviewed metadata, and frozen
  exports as separate artifacts
- prefer reviewable rectangle-based support surfaces over open-ended 3D authoring
- use AI2-THOR as a semantic prior, not as the final authority
- keep `vgm-assets` local schemas ahead of any `vgm-protocol` proposal
- make the first success criterion a tiny accepted slice, not broad coverage
- design the human-review tooling for EC2-hosted browser use, not local desktop
  assumptions

## Immediate Inputs

- `docs/architecture/support_surface_semantics_v1.md`
- `docs/architecture/support_clutter_prop_metadata_v0.md`
- `docs/plans/support_surface_semantics_v1_plan.md`
- `docs/plans/support_clutter_v0_plan.md`
- `docs/plans/objaverse_furniture_ingestion_v0_plan.md`
- `/home/ubuntu/scratch/repos/ai2thor/ai2thor/tests/data/metadata-schema.json`
- `/home/ubuntu/scratch/repos/ai2thor/unity/Assets/DebugTextFiles/PlacementRestrictions.txt`

## Phase 1: Freeze The Metadata Contract

Define one local `vgm-assets` annotation contract for object semantics.

The first contract should stay intentionally small.

Required object-level fields:
- `asset_id`
- `category`
- `front_axis`
- `up_axis`
- `bottom_support_plane`
- `placement_class`
- `review_status`
- `review_notes`

Required parent-object extension:
- `supports_objects`
- `support_surfaces_v1`

For `support_surfaces_v1`, support only rectangle-shaped surfaces in `v0`.

Required support-surface fields:
- `surface_id`
- `surface_type`
- `surface_class`
- `width_m`
- `depth_m`
- `height_m`
- `local_center_m`
- `normal_axis`
- `front_axis`
- `usable_margin_m`
- `review_status`

Required child-object extension:
- `base_shape`
- `base_width_m`
- `base_depth_m`
- `support_margin_m`
- `allowed_surface_types`
- `upright_axis`
- `stable_support_required`

Deliverables:
- local schema for object semantics annotations
- validator command and tests
- one small example annotation artifact for parent objects
- one small example annotation artifact for child objects

Stop/go boundary:
- the contract is stable enough that both auto-seeding and the explorer can use
  it without inventing a second format

## Phase 2: Build The AI2-THOR Auto-Seeding Path

Use AI2-THOR to generate candidate annotations for a tiny selected slice.

AI2-THOR should seed:
- category prior from `objectType`
- support prior from `receptacle`
- child-object prior from `pickupable` and `moveable`
- coarse compatibility priors from `PlacementRestrictions.txt`
- bounds and orientation hints from bounding-box metadata
- candidate support-surface rectangles for obvious tabletop or shelf assets

AI2-THOR should not be treated as final truth for:
- front direction of arbitrary meshes
- exact usable support extents
- real source-specific category cleanup
- reviewed placement semantics

Deliverables:
- a small AI2-THOR source-selection file
- a preprocessing script that writes candidate object-semantics annotations
- versioned candidate artifacts under a clear review-ready location
- validation tests for the candidate artifact shape

Stop/go boundary:
- reviewers can open a candidate annotation artifact and mostly correct it
  rather than authoring metadata from scratch

## Phase 3: Build Explorer v0 For EC2

Build a small EC2-hosted browser review tool against the same annotation
artifact written in Phase 2.

The explorer should not try to be a general-purpose 3D editor.

Explorer v0 requirements:
- load one asset at a time
- render the mesh and preview image
- show object-local axes and bounds
- show seeded `support_surfaces_v1` rectangles as overlays
- allow editing `front_axis`, `up_axis`, and `bottom_support_plane`
- allow adding or adjusting rectangle support surfaces
- allow editing category, placement class, and review status
- save reviewed annotations back to JSON

Recommended interaction model for `support_surfaces_v1`:
- auto-seed a candidate rectangle
- show it in 3D
- also show a plane-aligned top-down editing view
- let the reviewer resize, translate, and relabel the rectangle
- avoid arbitrary polygon drawing in `v0`

Infrastructure recommendation:
- host the explorer close to the assets on EC2
- keep the reviewer workflow browser-based
- do not require local desktop GPU setup or remote-desktop tooling

Deliverables:
- `Explorer v0` architecture note
- one minimal service or app that reads candidate artifacts and writes reviewed
  artifacts
- one saved reviewed annotation example from a real asset

Stop/go boundary:
- one reviewer can complete a full review loop in a browser with no manual JSON
  editing

## Phase 4: Add Review Queue v0

Once the explorer can edit one asset, add the smallest useful review queue.

Queue capabilities:
- list assets by source, category, and review status
- open the next asset needing review
- mark `reviewed`, `uncertain`, or `rejected`
- store brief reviewer notes

The queue should remain workflow glue around the same annotation artifacts.
It should not introduce a parallel metadata model.

Deliverables:
- queue artifact or service-level queue state
- status vocabulary and reviewer note conventions
- one documented reviewer workflow

Stop/go boundary:
- a small team can review a bounded slice consistently on EC2

## Phase 5: Export Only Reviewed Slices

After the review loop works, connect it to frozen exports.

The export rule should be strict:
- only reviewed or explicitly accepted assets are promoted downstream
- auto-seeded-only assets stay out of frozen scene-engine handoffs

Deliverables:
- filtered reviewed annotation export path
- one reviewed parent-object slice
- one reviewed child-object slice
- one tiny downstream scene-engine validation slice

Stop/go boundary:
- scene-engine can consume a reviewed slice without asset-specific hacks

## First Benchmark Slice

Do not start with hundreds of assets.

Start with a slice small enough to review carefully:

Parent objects:
- `coffee_table`
- `side_table`
- `bookshelf`

Child objects:
- `mug`
- `book`
- `bowl`

This slice is large enough to test:
- support-surface metadata
- child placement metadata
- parent-child compatibility
- the review workflow
- the frozen export seam

## Non-Goals

For this plan, do not:
- redesign `vgm-protocol`
- build a full DCC-style 3D editor
- support arbitrary support polygons
- bulk-ingest large numbers of objects before review works
- infer final semantics from AI2-THOR without human verification
- couple downstream scene placement directly to unreviewed candidate metadata

## Risks And Mitigations

Risk: the metadata contract grows too quickly.
Mitigation: freeze a very small `v0` contract and keep richer ideas in notes
until a real reviewed slice proves the need.

Risk: the explorer becomes a large product project.
Mitigation: keep `Explorer v0` single-asset, browser-based, and rectangle-only
for support surfaces.

Risk: AI2-THOR priors are over-trusted.
Mitigation: treat AI2-THOR output as candidate annotations only, never frozen
truth.

Risk: reviewers spend too much time hand-authoring geometry.
Mitigation: seed candidate axes and support rectangles automatically and make
review mostly correction-oriented.

Risk: EC2-hosted review becomes operationally heavy.
Mitigation: start with a small internal service and flat-file JSON artifacts
before adding databases or broader infrastructure.

## Recommended Immediate Next Steps

Do only these next:

1. write the local object-semantics annotation schema
2. define one example parent-object annotation artifact
3. define one example child-object annotation artifact
4. implement a tiny AI2-THOR candidate-writer for the benchmark slice
5. write a short `Explorer v0` architecture note against that artifact shape

## Success Criteria

We should consider this plan on track when all of the following are true:
- one shared local annotation contract exists
- AI2-THOR can write candidate annotations for the benchmark slice
- one reviewer can edit and save reviewed annotations on EC2 in a browser
- one reviewed slice can be exported cleanly for downstream use

## Development Log

- 2026-03-24: wrote the first cross-cutting plan tying metadata contract,
  AI2-THOR auto-seeding, and EC2-hosted human review into one `vgm-assets`
  pipeline.
