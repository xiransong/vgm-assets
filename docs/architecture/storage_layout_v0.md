# Storage Layout v0

This note defines how `vgm-assets` separates repo metadata from asset payloads.

## Principles

- keep code, docs, metadata, and selection specs in the repo
- keep raw source payloads outside the repo under `RAW_DATA_ROOT`
- keep unpacked and normalized derived payloads outside the repo under
  `DATA_ROOT`
- treat `RAW_DATA_ROOT` as immutable registered input data
- treat `DATA_ROOT` as reproducible derived data

## Default Roots

By default, `vgm-assets` uses:

- `RAW_DATA_ROOT=~/scratch/data/vgm/vgm-assets`
- `DATA_ROOT=~/scratch/processed/vgm/vgm-assets`

These can be overridden with:

- `VGM_ASSETS_RAW_DATA_ROOT`
- `VGM_ASSETS_DATA_ROOT`

## Kenney Layout

For the current Kenney Furniture Kit path, the canonical layout is:

```text
RAW_DATA_ROOT/
  sources/
    kenney/
      furniture_kit/
        kenney_furniture-kit.zip
        source_manifest.json

DATA_ROOT/
  sources/
    kenney/
      furniture_kit/
        unpacked/
        normalized/
          living_room_v0/
            selection_manifest.json
            sofa/
            coffee_table/
            tv_stand/
            bookcase/
            armchair/
            side_table/
            floor_lamp/
```

## Objaverse Metadata Layout

For the first Objaverse metadata-only path, the canonical layout should be:

```text
RAW_DATA_ROOT/
  sources/
    objaverse/
      metadata/
        furniture_v0/
          raw/
            <metadata artifact>
          source_manifest.json

DATA_ROOT/
  sources/
    objaverse/
      furniture_v0/
        metadata_harvest/
        review_queue/
```

This keeps the first Objaverse step lightweight and reproducible before any
geometry payload acquisition is introduced.

## Reproducibility Contract

Given:

- the expected raw archive in `RAW_DATA_ROOT`
- the repo-side source spec in `sources/kenney/source_spec_v0.json`
- the repo-side selection file in `sources/kenney/selection_v0.json`

the repo scripts should be able to rebuild the Kenney unpacked tree and the
normalized `living_room_v0` slice in `DATA_ROOT`.

## File Ref Rule

Repo-owned catalogs should not hardcode machine-specific absolute payload paths.

For `vgm-assets v0`:

- `files.*.path` in repo catalogs should be stored relative to `DATA_ROOT`
- local tools should resolve those refs against `DATA_ROOT` at runtime
- derived reports may record resolved absolute paths when needed for inspection

This keeps repo metadata portable across machines while still allowing local
tooling to work with the actual payload files on disk.
