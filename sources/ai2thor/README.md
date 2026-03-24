# AI2-THOR Source Notes

This directory records the `vgm-assets` source-side planning artifacts for
AI2-THOR-derived assets.

Current scope:
- first support-aware clutter props
- `mug`
- `book`
- first object-semantics benchmark slice

This is intentionally a small `v0` slice. It does not try to mirror the whole
AI2-THOR simulator or asset tree.

## Current Recommendation

For `support_clutter_v0_r1`, AI2-THOR is the recommended first source for:
- `mug`
- `book`

See:
- `docs/architecture/support_clutter_prop_source_selection_v0.md`

## Current Planning Artifacts

- `sources/ai2thor/support_clutter_selection_v0.json`
- `sources/ai2thor/object_semantics_selection_v0.json`

## Current Raw Staging Paths

The repo now supports two narrow AI2-THOR staging paths:

- `register-ai2thor-support-clutter-selection`
- `register-ai2thor-object-semantics-selection`

The object-semantics benchmark slice can be staged with:

```bash
./scripts/sources/stage_ai2thor_object_semantics_v0.sh
```

Its processed review workspace can be refreshed with:

```bash
./scripts/review/refresh_ai2thor_object_semantics_workspace_v0.sh
```

## Local Upstream Repo

Current expected local source checkout:

- `/home/ubuntu/scratch/repos/ai2thor`

The first slice relies on local source-relative paths beneath:

- `unity/Assets/Physics/SimObjsPhysics/Kitchen Objects/Mug/`
- `unity/Assets/Physics/SimObjsPhysics/Bedroom Objects/Book/`

## Notes

- The currently staged AI2-THOR paths are still intentionally narrow.
- They do not yet cover the whole AI2-THOR simulator asset corpus.
- Before broader redistribution, we should recheck whether the repo-level
  `Apache-2.0` license fully covers the specific source assets we normalize.
