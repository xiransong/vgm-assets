# Object Semantics Explorer v0

This note defines the first internal explorer for human review of object
semantics in `vgm-assets`.

The explorer is the bridge between:

- auto-seeded candidate annotations
- human semantic review
- frozen reviewed annotation artifacts

It is intentionally small and repo-local for now.

## Purpose

The first object-semantics pipeline should not rely on:

- raw JSON editing
- local desktop DCC workflows
- remote desktop access into EC2

Instead, reviewers should be able to open one asset in a browser, inspect the
current candidate metadata, adjust the fields we care about, and save the
result back into the same annotation format.

## Why This Exists

For the benchmark slice, we now have a real candidate artifact:

- `catalogs/object_semantics_v0/ai2thor_candidate_annotations_v0.json`

That artifact is useful, but not trustworthy enough to export downstream
without review.

The explorer exists to turn:

- `review_status = auto`
- `review_status = uncertain`

into:

- `review_status = reviewed`
- or an explicit keep/reject decision later

without inventing a second annotation format.

## Core Rule

The explorer must read and write the same local contract:

- `schemas/local/object_semantics_annotation_set_v0.schema.json`

It should not introduce a parallel UI-only model.

## Scope

`Explorer v0` is a single-asset review tool.

It is not yet:

- a full review queue product
- a multi-user workflow system
- a general 3D editor
- a scene-layout tool

## Hosting Model

The explorer should be designed for EC2-hosted use.

Recommended deployment shape:

- lightweight Python backend in `vgm-assets`
- static browser client served by that backend
- reviewers connect from a normal web browser
- asset files stay near the data on EC2

This avoids dependence on:

- local workstation GPU setup
- Blender on reviewers' laptops
- remote desktop or X forwarding workflows

## Recommended Minimal Stack

For `v0`, keep the stack intentionally small.

Recommended backend:

- `fastapi`
- `uvicorn`

Recommended frontend:

- static `HTML`
- minimal `JavaScript`
- `three.js` for mesh viewing

Avoid for `v0` unless clearly needed:

- React
- Next.js
- databases
- authentication systems
- background job systems

## Input Artifacts

The explorer should start from one candidate annotation artifact, such as:

- `catalogs/object_semantics_v0/ai2thor_candidate_annotations_v0.json`

Each asset record in that file should be opened independently for review.

The explorer also needs access to the source mesh path and any preview image
available for the currently reviewed asset.

For the first AI2-THOR benchmark slice, the source selection file is:

- `sources/ai2thor/object_semantics_selection_v0.json`

The explorer backend can use that selection file to resolve the source prefab
and model location for each seeded asset.

## Output Artifacts

`Explorer v0` should write reviewed annotations back into the same schema.

Recommended first output path:

- `catalogs/object_semantics_v0/ai2thor_reviewed_annotations_v0.json`

This keeps the stage boundary explicit:

- candidate annotations
- reviewed annotations

Both may exist at the same time.

## Review States

For `v0`, the explorer should preserve the current schema vocabulary:

- `auto`
- `reviewed`
- `uncertain`
- `rejected`

Recommended meaning in the UI:

- `auto`
  - seeded automatically and untouched by a reviewer
- `reviewed`
  - a reviewer explicitly accepted the current fields
- `uncertain`
  - the reviewer believes more inspection is needed
- `rejected`
  - the asset should not move forward in the current slice

## Explorer Workflow

The first workflow should be:

1. open one asset
2. inspect mesh and current metadata
3. adjust semantics
4. save the updated annotation
5. move to the next asset later through a separate queue or simple file list

This keeps the explorer and the future review queue loosely coupled.

## Required UI Features

`Explorer v0` should support:

- load one asset by `asset_id`
- render the asset mesh
- show a preview image if available
- show object-local axes
- show the current bottom support plane
- show current `support_surfaces_v1` overlays
- edit object-level semantics
- edit parent support surfaces
- edit child placement metadata
- edit `review_status`
- edit short `review_notes`
- save the updated annotation record

## Object-Level Fields To Edit

The UI should expose:

- `category`
- `front_axis`
- `up_axis`
- `bottom_support_plane`
- `placement_class`
- `review_status`
- `review_notes`

For `v0`, it is acceptable for some fields to be dropdown or numeric-form
driven rather than manipulated directly in 3D.

## Parent-Object Editing

For `asset_role = parent_object`, the explorer should expose:

- `supports_objects`
- `support_surfaces_v1`

The first parent categories are:

- `coffee_table`
- `side_table`
- `bookshelf`

### `support_surfaces_v1` Interaction Model

This is the most important design constraint:

- do not support arbitrary polygons in `v0`
- do not ask reviewers to paint directly on triangles
- support only rectangle surfaces

The intended workflow is:

1. show the seeded rectangle surface in the 3D viewer
2. show the same surface in a plane-aligned editing view
3. let the reviewer:
   - move the rectangle
   - resize width and depth
   - adjust height
   - relabel `surface_type` and `surface_class`
   - edit `usable_margin_m`
4. save the updated rectangle

Required editable support-surface fields:

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
- `supports_categories`
- `placement_style`
- `review_status`

## Child-Object Editing

For `asset_role = child_object`, the explorer should expose:

- `child_placement.base_shape`
- `child_placement.base_width_m`
- `child_placement.base_depth_m`
- `child_placement.support_margin_m`
- `child_placement.allowed_surface_types`
- `child_placement.upright_axis`
- `child_placement.stable_support_required`
- `child_placement.placement_style`

The first child categories are:

- `mug`
- `book`
- `bowl`

For these first categories, a side-panel form is sufficient.

## Minimal Backend API

The backend can stay extremely small.

Recommended first endpoints:

- `GET /api/object-semantics/assets`
  - list asset ids and summary review state from one annotation artifact
- `GET /api/object-semantics/assets/{asset_id}`
  - return one annotation record plus resolved mesh and preview refs
- `POST /api/object-semantics/assets/{asset_id}`
  - validate and persist one updated annotation record
- `GET /api/object-semantics/schema`
  - optional debug endpoint for the local schema version

The backend should validate every saved record against:

- `schemas/local/object_semantics_annotation_set_v0.schema.json`

## File Persistence Rule

The explorer should not edit the candidate artifact in place by default.

Instead:

- read from candidate annotations
- write to a reviewed artifact

This preserves:

- provenance
- ability to compare before/after review
- reproducibility of auto-seeded output

## Benchmark Slice

The first explorer milestone should target only the current benchmark slice:

- `ai2thor_coffee_table_01`
- `ai2thor_side_table_01`
- `ai2thor_bookshelf_01`
- `ai2thor_mug_01`
- `ai2thor_book_01`
- `ai2thor_bowl_01`

The current candidate artifact already contains a useful edge case:

- `ai2thor_bookshelf_01`

This asset is intentionally marked `uncertain`, so the explorer should make it
easy to inspect and correct rather than hiding the ambiguity.

## Non-Goals

For `v0`, do not add:

- multi-asset scene review
- collaborative editing
- authentication
- annotation history UI
- arbitrary polygon support-surface authoring
- mesh repair or mesh editing
- downstream export logic inside the explorer

Those belong later, after the single-asset review loop works.

## Success Criteria

`Explorer v0` is successful when:

- one reviewer can open a candidate asset on EC2 in a browser
- the reviewer can inspect the mesh and overlays
- the reviewer can edit object-level fields and support rectangles
- the saved result validates against the existing local schema
- reviewed annotations can be kept separate from candidates

## Recommended Immediate Next Step

Implement only this next:

1. a short backend note for routes and storage layout
2. a minimal `FastAPI + three.js` scaffold
3. support for loading the six-asset AI2-THOR benchmark slice
4. save one reviewed annotation artifact for that slice
