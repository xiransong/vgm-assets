# Category Sampling v0

This note defines the `v0` asset-sampling policy for downstream scene
generation that consumes `vgm-assets` catalogs.

## Policy

Sampling is currently:

- category-aware
- uniform within category
- reproducible when a fixed random seed is used

The intended `v0` flow is:

1. scene logic decides which category is needed
2. all valid assets in that category are collected
3. one asset is sampled uniformly at random from that set

## Why Uniform

Uniform sampling is the right default for the current catalog state because:

- the catalog is still small and manually curated
- there is no strong empirical basis yet for non-uniform priors
- equal treatment is easy to explain and debug
- it avoids locking in arbitrary early bias

## Current Relationship To `sample_weight`

`AssetSpec.sample_weight` remains available in the catalog schema, but
`vgm-assets v0` does not treat it as the active sampling rule.

For `v0`:

- sampling should be interpreted as uniform within category
- equal `sample_weight` values are acceptable metadata
- downstream repos should not introduce weighted sampling unless that policy is
  explicitly revised

## Scope

This note only defines how to choose among assets that already satisfy the
current category and any scene-level validity constraints.

It does not define:

- how categories are chosen
- how scene-specific validity filtering is implemented
- how future learned or empirical sampling priors should work

## Export Artifact

For downstream consumers that only need category-level asset lookup, `vgm-assets`
can emit a compact category index JSON that records:

- category name
- sampling policy
- asset count
- ordered asset id list

For the current Kenney living-room slice, this artifact is:

- `catalogs/living_room_kenney_v0/category_index.json`
