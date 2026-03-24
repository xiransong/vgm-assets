# VGM Custom Asset Generation vs Infinigen v0

This short note explains why `vgm` may eventually need its own 3D asset
generation tool, even though Infinigen is already a strong open-source indoor
generation system.

## Short Position

Infinigen is an excellent upstream source of procedural indoor assets and
scene-level semantics.

But for vision-grounded human motion generation, the research target is not
just "plausible indoor assets." The target is **assets with affordances and
contact-relevant structure that are accurate enough for human motion**.

That is where a `vgm`-specific asset generator can become valuable.

## What Infinigen Gives Well

Infinigen already provides:

- procedural generation for many indoor object families
- room and furniture semantics
- scene-level placement logic
- useful tagging and segmentation machinery
- some support-surface style tags for certain assets
- strong diversity and controllable randomization

This makes Infinigen a very attractive source for:

- background scene assets
- broad category coverage
- diversity beyond a small hand-authored asset library
- bootstrapping object families before custom tools mature

## What VGM Ultimately Needs

For human motion research, some assets are more than visual props. They are
**interaction targets**.

Examples:

- a chair that should support sitting
- a sofa with a meaningful seat region and back support
- a table with a reliable top support surface
- a bucket or box with a handle that matters for grasping

For these objects, we do not only need category labels. We need precise,
stable, machine-usable structure such as:

- front direction
- up direction
- seat surface
- support surfaces
- bottom support region
- handle region
- back support plane
- contact-relevant dimensions

These annotations are central to downstream motion generation, not just nice
metadata extras.

## Why a Custom VGM Generator Can Be Better

The main advantage of a custom `vgm` asset generator is:

**annotation by construction**

Instead of recovering affordances from a finished mesh, the generator defines
the object from semantic parts and parameters.

That means:

- the seat surface is known because the seat was generated explicitly
- the support surface is known because the tabletop was generated explicitly
- the handle is known because the handle was generated explicitly
- the front direction is part of the canonical local frame
- the object dimensions are known from the generating parameters

This is especially attractive for:

- chairs
- armchairs
- sofas
- coffee tables
- side tables
- TV stands
- bookshelves
- handled containers

These are not too many object families, but they are very important for
human-object interaction.

## Why This Is Different From "Competing With Infinigen"

The goal is not to replace Infinigen.

The better framing is:

- **Infinigen** is a broad procedural asset and scene-generation system
- **a VGM custom generator** would be a narrow interaction-centric generator

So the two systems serve different priorities:

- Infinigen optimizes for broad procedural realism and scene diversity
- VGM custom generation would optimize for affordance fidelity, contact
  semantics, and motion-relevant annotations

In that sense, a VGM generator is not an alternative to Infinigen so much as a
specialized complement.

## Recommended Long-Term Direction

A good long-term strategy is a hybrid one:

- use custom VGM-generated assets for high-value interaction furniture and
  motion-critical objects
- use Infinigen and other open assets for broader background coverage, clutter,
  and decorative diversity

This gives the project:

- high annotation fidelity where human motion depends on it
- lower engineering burden overall
- continued access to open-source diversity

## Research Motivation

The research motivation is simple:

If the goal is realistic human motion around and with objects, then the most
important assets are not the ones that merely look plausible. The most
important assets are the ones whose **interaction structure is correct**.

That is why a custom `vgm` asset generator could become a strong long-term
research contribution:

- not just generating geometry
- but generating **interaction-ready assets with trusted affordance
  annotations**
