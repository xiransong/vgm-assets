# Objaverse Furniture Metadata Harvest v0

This note defines the first metadata-harvest artifact for Objaverse furniture
ingestion in `vgm-assets`.

The metadata harvest is the earliest structured artifact in the Objaverse path.
It comes before:

- license narrowing
- category narrowing
- review queue creation
- normalized bundle generation

## Purpose

The first Objaverse wave should start by collecting only metadata and lightweight
source facts.

That keeps the early pipeline:

- cheap
- reproducible
- auditable
- easy to rerun as policies evolve

## File Shape

The local validating schema for this table is:

- `schemas/local/objaverse_furniture_metadata_harvest_v0.schema.json`

Recommended repo-side artifact path:

- `sources/objaverse/metadata_harvest_template_v0.json`

Future generated outputs can follow the same shape under `DATA_ROOT`.

## Harvest Structure

The harvest artifact is a JSON object with:

- `harvest_id`
- `source_id`
- `created_at`
- `record_count`
- `records`

Each record represents one source-side Objaverse object entry before any local
accept/reject review decision.

## Required Record Fields

Each harvested record should minimally include:

- `object_uid`
- `source_url`
- `title`
- `license`

These are the minimum fields needed to support provenance and early license
gating.

## Recommended Record Fields

The first harvest table should also include:

- `source_tags`
- `source_categories`
- `description`
- `available_formats`
- `thumbnail_url`
- `metadata_path`
- `payload_ref`

These are the fields we are most likely to need for:

- keyword-based category mapping
- preview support
- selective fetch planning

## Optional Early Geometry Fields

If the source metadata already exposes them cheaply, the harvest may also carry:

- `triangle_count`
- `vertex_count`
- `bounds`

But these should stay optional in `v0`.

We do not want to require geometry inspection just to create the first harvest
artifact.

## Decision Rule

The harvest table is not a curation artifact.

It should not contain:

- `review_status`
- `review_notes`
- final local category assignment

Those belong in the later review queue.

## Non-Goals For v0

This artifact is not trying to be:

- a final accepted candidate list
- a normalized asset manifest
- a downstream scene-engine contract

It is only the structured source-metadata layer that feeds later narrowing.
