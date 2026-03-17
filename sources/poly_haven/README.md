# Poly Haven Source

This directory tracks the repo-side planning and source metadata for the first
Poly Haven-based room-surface material slice in `vgm-assets`.

No Poly Haven payloads are stored in the repo.

## Scope

The first Poly Haven integration is intentionally narrow:

- room-surface materials only
- `floor`, `wall`, and `ceiling` only
- a small manually curated pool

This source is not yet used for object-material normalization.

## Source Strategy

For `v0`, Poly Haven should be treated as:

- manually curated at the selection stage
- API-driven at the download stage
- normalized into backend-agnostic processed bundles under `DATA_ROOT`

The intended rule is:

- use the Poly Haven API for selected downloads
- send a project-specific `User-Agent`
- avoid scraping the website HTML

## Repo Files

- `source_spec_v0.json`
  - source-level expectations and storage layout
- `room_surface_selection_v0.json`
  - small curated room-surface material pool for the first snapshot

## Planned Data Layout

Raw source files:

```text
RAW_DATA_ROOT/
  sources/
    poly_haven/
      materials/
        source_manifest.json
        <material_id>/
          ...
```

Processed bundles:

```text
DATA_ROOT/
  materials/
    room_surfaces/
      poly_haven/
        <surface_type>/
          <material_id>/
            ...
```

## Current Status

As of `2026-03-17`, this directory contains planning artifacts only. No raw
downloads or processed material bundles have been created yet.
