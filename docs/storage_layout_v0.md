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

## Reproducibility Contract

Given:

- the expected raw archive in `RAW_DATA_ROOT`
- the repo-side source spec in `sources/kenney/source_spec_v0.json`
- the repo-side selection file in `sources/kenney/selection_v0.json`

the repo scripts should be able to rebuild the Kenney unpacked tree and the
normalized `living_room_v0` slice in `DATA_ROOT`.
