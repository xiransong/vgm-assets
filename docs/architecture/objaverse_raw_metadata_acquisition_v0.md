# Objaverse Raw Metadata Acquisition v0

This note defines the first raw-metadata acquisition contract for Objaverse
furniture ingestion in `vgm-assets`.

It intentionally covers metadata only.

We are not defining bulk geometry acquisition yet.

## Purpose

Before we download or register any real Objaverse data, we need a clear answer
to one simple question:

What is the first real raw input artifact?

For `v0`, the answer should be:

- a metadata-only source artifact

This keeps the first real Objaverse step:

- lightweight
- easy to verify
- easy to back up
- independent of heavy geometry transfer

## First Real Input

The first real input should be a metadata artifact that can be treated as an
immutable raw source under `RAW_DATA_ROOT`.

Examples of acceptable first inputs:

- one JSON metadata export
- one JSONL metadata dump
- one Parquet file if we later decide that is the most practical source form

For `v0`, prefer a JSON or JSONL export because it is easier to inspect and
debug manually.

## Raw Storage Contract

Recommended raw layout:

```text
RAW_DATA_ROOT/
  sources/
    objaverse/
      metadata/
        furniture_v0/
          raw/
            <metadata artifact>
          source_manifest.json
```

This should be treated the same way we treat the Kenney source zip:

- immutable once registered
- checksummed
- accompanied by a local source manifest

## Source Manifest Expectations

The raw metadata registration manifest should record:

- `source_name`
- `source_url`
- `acquired_at`
- `acquired_by`
- `acquisition_method`
- `canonical_filename`
- `size_bytes`
- `sha256`
- optional notes about the export scope

## Processed Output Direction

The first processed metadata-only outputs should live under `DATA_ROOT`, for
example:

```text
DATA_ROOT/
  sources/
    objaverse/
      furniture_v0/
        metadata_harvest/
        review_queue/
```

This keeps the early Objaverse path parallel to the Kenney and Poly Haven
storage model:

- raw inputs in `RAW_DATA_ROOT`
- reproducible derived artifacts in `DATA_ROOT`

## Reproducibility Rule

Given:

- the registered raw metadata artifact in `RAW_DATA_ROOT`
- the repo-side source spec
- the repo-side ingestion policy
- the repo-side narrowing contract

we should be able to regenerate:

- a metadata-harvest artifact
- a review queue artifact

without touching live external sources.

## Deliberate Non-Goals For v0

Not part of this first acquisition contract:

- bulk mesh payload download
- per-object texture download
- selective geometry mirroring
- normalization of real Objaverse meshes

Those come later, after the metadata-only path is solid.
