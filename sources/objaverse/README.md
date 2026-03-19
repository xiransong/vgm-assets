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
- `raw_metadata_source_spec_v0.json`
- `furniture_ingestion_policy_v0.json`
- `metadata_harvest_template_v0.json`
- `review_queue_template_v0.json`

## Current Raw Metadata Contract

The first raw-metadata acquisition contract is now defined by:

- `docs/architecture/objaverse_raw_metadata_acquisition_v0.md`
- `sources/objaverse/raw_metadata_source_spec_v0.json`

You can register a real raw metadata artifact with:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  register-objaverse-raw-metadata-source \
  sources/objaverse/raw_metadata_source_spec_v0.json \
  --raw-file /path/to/objaverse_furniture_metadata.jsonl
```

You can then import the registered raw artifact into a schema-valid
metadata-harvest file under `DATA_ROOT`:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  import-objaverse-furniture-metadata-harvest \
  sources/objaverse/raw_metadata_source_spec_v0.json
```

And you can generate a real review queue from that imported harvest:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  generate-objaverse-furniture-review-queue \
  sources/objaverse/raw_metadata_source_spec_v0.json \
  --harvest /path/to/imported_harvest.json \
  --policy sources/objaverse/furniture_ingestion_policy_v0.json
```

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

## Current Narrowing Contract

The first narrowing bridge from metadata harvest to review queue is now defined
by:

- `docs/architecture/objaverse_furniture_narrowing_v0.md`
- `sources/objaverse/narrowing_contract_v0.json`

You can validate a review queue with:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  validate-objaverse-furniture-review-queue \
  sources/objaverse/review_queue_template_v0.json
```

You can also exercise the current stub narrowing seam:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  write-stub-objaverse-furniture-review-queue \
  --harvest sources/objaverse/metadata_harvest_template_v0.json \
  --policy sources/objaverse/furniture_ingestion_policy_v0.json \
  --output /tmp/objaverse_review_queue_stub.json
```

The repo also carries a mock metadata harvest for testing the first real
narrowing pass without live downloads:

- `sources/objaverse/mock_metadata_harvest_v0.json`
- `sources/objaverse/mock_review_queue_v0.json`

You can run the current rule-based narrowing pass with:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  narrow-objaverse-furniture-harvest \
  --harvest sources/objaverse/mock_metadata_harvest_v0.json \
  --policy sources/objaverse/furniture_ingestion_policy_v0.json \
  --output sources/objaverse/mock_review_queue_v0.json
```

## Current Real-Shard Review State

The first official metadata shard has now been processed through the
metadata-only pipeline and reviewed manually.

Repo-side review artifacts:

- `docs/catalogs/objaverse_000_014_review_v0.md`
- `sources/objaverse/manual_review_objaverse_000_014_v0.json`
- `sources/objaverse/selective_geometry_objaverse_000_014_v0.json`

You can resolve that accepted shortlist against an imported harvest artifact and
write a selective-geometry manifest with:

```bash
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  write-objaverse-selective-geometry-manifest \
  --selection sources/objaverse/selective_geometry_objaverse_000_014_v0.json \
  --harvest /path/to/imported_harvest.json \
  --output sources/objaverse/selective_geometry_manifest_objaverse_000_014_v0.json
```

The next acquisition step should remain selective:

- fetch geometry only for the accepted shortlist
- do not bulk-download held candidates yet
- inspect real payload quality before creating normalized bundles

## Expected Future Output

If this source path works, it should eventually feed:

- `catalogs/living_room_objaverse_v0/`
- `exports/scene_engine/living_room_objaverse_v0_r1/`

without modifying the current Kenney snapshots.
