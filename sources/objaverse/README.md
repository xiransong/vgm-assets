# Objaverse Source Intake

This folder tracks the first large-scale furniture-diversity plan for
`vgm-assets` using Objaverse-family sources.

It stores repo-side metadata and policy only. It does not store source payloads.

## Why Objaverse

Kenney remains the stable bootstrap source, but Objaverse is the most promising
next source for scaling furniture diversity toward hundreds or thousands of
candidates.

The main reason to use it is scale.

The main reason to move carefully is that per-object license and quality vary
substantially.

## Current Policy

The current Objaverse direction is intentionally strict:

- start with metadata-first filtering
- allow only `CC0` and `CC-BY 4.0` in the first wave
- stay within the current living-room furniture taxonomy
- defer bulk geometry download until the review queue format is frozen

## Planned Repo-side Files

- `source_spec_v0.json`
- `furniture_ingestion_policy_v0.json`
- `metadata_harvest_template_v0.json`
- `review_queue_template_v0.json`

## Current Metadata Contract

The first metadata-harvest contract is now defined by:

- `docs/architecture/objaverse_furniture_metadata_harvest_v0.md`
- `schemas/local/objaverse_furniture_metadata_harvest_v0.schema.json`

The repo-side starter template is:

- `sources/objaverse/metadata_harvest_template_v0.json`

You can validate a harvest artifact with:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  validate-objaverse-furniture-metadata-harvest \
  sources/objaverse/metadata_harvest_template_v0.json
```

## Current Review Contract

The first review-queue contract is now defined by:

- `docs/architecture/objaverse_furniture_review_queue_v0.md`
- `schemas/local/objaverse_furniture_review_queue_v0.schema.json`

The repo-side starter template is:

- `sources/objaverse/review_queue_template_v0.json`

You can validate a review queue with:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  validate-objaverse-furniture-review-queue \
  sources/objaverse/review_queue_template_v0.json
```

## Expected Future Output

If this source path works, it should eventually feed:

- `catalogs/living_room_objaverse_v0/`
- `exports/scene_engine/living_room_objaverse_v0_r1/`

without modifying the current Kenney snapshots.
