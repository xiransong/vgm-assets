# Material Packaging v0

This note records the first material policy for `vgm-assets`.

## Goal

Keep material packaging simple enough for the first real open-source asset
slice, while leaving room for more renderer-specific handling later.

## First Recommendation

Use Poly Haven as the first approved material source.

References:
- <https://polyhaven.com/>
- <https://polyhaven.com/license>

## Packaging Rule

For `v0`, treat materials as optional payloads attached to normalized assets.

That means:
- an asset can exist in the catalog without material files
- if material files are included, they should be recorded explicitly in asset
  metadata through `files`
- material packaging should stay backend-agnostic at the protocol boundary

## Backend-Agnostic Minimum

For the first real asset slice, the repo should preserve:
- base color / albedo texture when present
- normal texture when present
- roughness texture when present
- metalness texture when present
- a simple preview image when possible

The protocol does not yet define dedicated material fields, so these should
remain internal packaging details until we know what downstream repos need.

## Repo Rule

Do not extend `vgm-protocol` for material-specific payload schemas yet.

First answer these practical questions inside `vgm-assets`:

1. can we normalize material layouts consistently across sources?
2. what files do downstream repos actually need?
3. do we need one generic material bundle ref or named texture refs?

## Immediate Next Step

For the first Kenney-backed furniture slice:

- allow no-material or minimal-material normalized packages
- add one Poly Haven-backed material experiment for one asset only
- document the resulting file layout before broadening material support
