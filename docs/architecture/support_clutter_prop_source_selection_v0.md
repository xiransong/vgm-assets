# Support Clutter Prop Source Selection v0

This note records the recommended first source choice for the initial
support-aware clutter bridge in `vgm-assets`.

Scope:
- `mug`
- `book`

Target milestone:
- `support_clutter_v0_r1`

## Recommendation

Use **AI2-THOR as the first practical source for both `mug` and `book`**.

This is not a general claim that AI2-THOR should replace Objaverse for all
future clutter or furniture work. It is a narrow decision for the smallest
first bridge.

## Why This Is The Best First Move

For the current milestone, we do not need hundreds of prop assets yet. We need:
- `2-3` mugs
- `3-5` books

AI2-THOR already appears to provide enough local source material for that.

### Mug

The local repo already contains directly relevant mug assets, including:
- kitchen mug prefabs:
  - `Mug_1`
  - `Mug_2`
  - `Mug_3`
- RoboTHOR mug prefabs:
  - `RoboTHOR_mug_ai2_1_v`
  - `RoboTHOR_mug_ai2_2_v`

And corresponding source models:
- `unity/Assets/Physics/SimObjsPhysics/Kitchen Objects/Mug/Models/mugs_grp.fbx`
- `unity/Assets/Physics/SimObjsPhysics/RoboTHOR Objects/RoboTHOR_Assets_SmallObjects/Target_SmallObjects/Mug/Models/RoboTHOR_mugs_grp.fbx`

This is already enough to meet the first bridge target.

### Book

AI2-THOR is especially strong for books.

The local repo contains many directly relevant book prefabs, including:
- bedroom book prefabs:
  - `Book_1` through `Book_30`
- RoboTHOR book prefabs:
  - `RoboTHOR_book_ai2_1_v` through `RoboTHOR_book_ai2_6_v`

And corresponding source models:
- `unity/Assets/Physics/SimObjsPhysics/Bedroom Objects/Book/Models/books_grp.fbx`
- `unity/Assets/Physics/SimObjsPhysics/RoboTHOR Objects/RoboTHOR_Assets_SmallObjects/Background_SmallObjects/Book/Models/RoboTHOR_books_grp.fbx`

So for books, AI2-THOR gives us much more than the `3-5` assets needed for the
first bridge.

## Why Not Start With Objaverse Here

Objaverse is still the right long-term source for scale and diversity, but it
is not the smallest practical path for this specific milestone.

Reasons:
- the current bridge only needs two prop categories
- we already have AI2-THOR locally
- AI2-THOR is semantically aligned with embodied support/receptacle behavior
- using AI2-THOR avoids reopening a larger metadata-review-download loop just
  to bootstrap `mug` and `book`

Objaverse should remain the follow-on source when we want:
- many more prop categories
- large diversity within categories
- scale beyond the first bridge

## Why Not Start With Kenney Here

Kenney is excellent for bootstrapping, but for `mug` / `book` clutter it is
less attractive than AI2-THOR:
- more stylized
- less semantically aligned with embodied indoor clutter
- not obviously better than the AI2-THOR local asset set we already have

So Kenney is not the preferred first prop source for this bridge.

## Practical First Slice

Recommended `support_clutter_v0_r1` source subset:

### Mug

Prefer this order:
1. `Mug_1`
2. `Mug_2`
3. `Mug_3`

Optional later additions:
- `RoboTHOR_mug_ai2_1_v`
- `RoboTHOR_mug_ai2_2_v`

### Book

Prefer a small handpicked subset from the bedroom book set:
1. `Book_1`
2. `Book_5`
3. `Book_9`
4. `Book_13`
5. `Book_24`

These should be reviewed visually before normalization, but they are already a
good first candidate pool.

## Current Recommendation

For `support_clutter_v0_r1`, do this:
1. ingest AI2-THOR `mug` and `book` assets first
2. build the first tiny prop slice and compatibility export
3. validate the full bridge in `vgm-scene-engine`
4. only then decide whether to add Objaverse prop diversity
