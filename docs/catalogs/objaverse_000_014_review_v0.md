# Objaverse 000-014 Review v0

This note records the first manual review pass over the real Objaverse review
queue generated from:

- `DATA_ROOT/sources/objaverse/furniture_v0/metadata_harvest/objaverse_000-014_harvest.json`
- `DATA_ROOT/sources/objaverse/furniture_v0/review_queue/objaverse_000-014_review_queue.json`

## Scope

This is a metadata-only review pass.

We are not yet downloading or inspecting real geometry payloads, so the
decisions here are intentionally conservative.

## Queue Summary

After the first quality-filter pass, the `000-014` shard produced:

- `16` review candidates

Category breakdown:

- `sofa`: 9
- `armchair`: 3
- `bookshelf`: 1
- `bookcase`: 1
- `coffee_table`: 1
- `side_table`: 1

## Review Outcome

For the first normalization prototype, the most promising near-term candidates
are:

- `ac9ef69e1bbf4258aa489635b6cec609` `Earmes Lounge Chair`
- `c715fad78e6c4fc79b3b54d40ab50d07` `Leather and Fabric Sofa`
- `08d58a4f9c8e4a90b52cec383e05b662` `table 70s`
- `2daabc422a2e46f489f31c4a3b2b4d54` `Bookshelf`
- `415990b9b8d7434099682efbc9993132` `nightstand`

These are still only metadata-level accepts. They are good first candidates for
the next geometry-backed prototype because they are:

- category-aligned
- not obviously damaged or stylized joke assets
- not obviously full-room scenes
- not immediately disqualified by strange titles or descriptions

## Conservative Holds

The following are plausible, but I would hold them until we inspect real
geometry:

- `cc62391ab66141119f769c20b07a1c11` `new_Armchair`
- `c6e26c415f484c24b844c95de2d4e9fe` `armchair`
- `b7291e4a38de4be4a3aa88689bd51f9f` `Bookcase`
- `3079f5cc61ea4acb9bdc3d304025b3e2` `Sofa`
- `065afa72464b47c7911493811233b362` `Shihba - SSC210`
- `90033ea46d90407d9bcc8318186a2b1e` `CLASSIC - MODERN - LEATHER SOFA`
- `b60aa915efb34b3ebd44b18403b1b040` `Clients_3_Sofa_2 - CSM239`
- `447a958614524af09826c60303e445b3` `Sofa Kenni_Pawsome`

Most of these are held because they look potentially useful but also carry at
least one risk:

- very high triangle count
- 3D-scanned source with possible cleanup burden
- generic or weak metadata
- possible mismatch between title and actual isolated furniture quality

## Current Rejects

The following look weak enough to reject at the metadata stage:

- `7d4849b06fcf4e78bdf755902ca68a10` `Диван`
- `4ed826ac8a8e4e3a98e23d7afb9b0813` `Sofa`
- `581c76292490419481b44621e13746f5` `Projeto Sala`

Reasons:

- `Диван`
  - title is fine, but the description is noisy and low-signal enough that I
    would not prioritize it over stronger sofa candidates
- `Sofa` (`4ed826...`)
  - very low triangle count and generic metadata; likely too weak for the first
    realism-oriented wave
- `Projeto Sala`
  - likely a room-scene export rather than a clean single furniture asset

## Recommendation

The clean next prototype should not start from all `16` candidates.

It should start from the `5` accepted metadata candidates above, because that is
already enough to test:

- selective geometry registration
- first normalized Objaverse furniture bundles
- first `living_room_objaverse_v0` slice planning
