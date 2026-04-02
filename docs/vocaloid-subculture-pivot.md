# Vocaloid / Subculture Pivot

## New Product Goal

Build a reusable engine that generates `Suno-ready song packages` for the Vocaloid / subculture lane, with a primary reference axis around `PinocchioP` and `DECO*27`.

The target output is not a raw lyric draft in isolation. The target output is:

1. `style prompt`
2. `full lyric`
3. `quality score + selection rationale`

## Why This Direction Is Better

The previous broad J-pop direction was too wide.

- artist variance was too high
- mode boundaries were too soft
- the rule-based renderer kept collapsing into generic J-pop

The Vocaloid / subculture lane is narrower and more regular.

- hook language is more compressed
- concept words matter more
- irony / confession / breakdown modes are easier to separate
- title and chorus slogan behavior is stronger and easier to benchmark

## Primary Reference Axis

### PinocchioP

Use as the anchor for:

- ironic meta writing
- social commentary through distorted slogans
- conceptual hooks
- uneasy but catchy phrase design

### DECO*27

Use as the anchor for:

- direct emotional hook writing
- relationship-centric vocaloid pop
- modern compressed chorus writing
- repeatable singable slogan structures

## Initial Mode Taxonomy

### 1. ironic_meta

Reference gravity:

- PinocchioP-heavy

Core traits:

- cynical or self-aware narrator
- concept-heavy nouns
- social discomfort
- slogan-like hook line
- unstable but catchy phrasing

### 2. direct_emotional_pop

Reference gravity:

- DECO*27-heavy

Core traits:

- direct address
- emotional clarity
- relationship tension
- shorter, cleaner chorus lines
- strong title-to-hook binding

### 3. dark_cute_breakdown

Reference gravity:

- hybrid lane

Core traits:

- cute surface vs unstable emotional core
- sweet-to-toxic flip
- breakdown / glitch / collapse imagery
- aggressive chorus release

## Anchor Strategy

Do not try to solve a whole discography first.

Use:

- `10 PinocchioP anchor tracks`
- `10 DECO*27 anchor tracks`

Start with `20 total` high-value anchor tracks and treat them as the main benchmark set.

## Engine Boundary

The internal engine should own:

- conditioning record structure
- section planning
- mode routing
- prompt package generation
- critic / rerank / benchmark

The internal engine should not be treated as the final sentence-level lyric writer.

Sentence generation should be external-model-first.

## Development Rule

From this point on:

- `Ado` is a historical benchmark, not the main product target
- all new mainline planning should optimize for Vocaloid / subculture modes
- track-specific hacks should be avoided unless they become reusable mode rules

## Immediate Next Steps

1. create `pinocchiop` and `deco27` artist scaffolds
2. define a shared `subculture mode profile`
3. collect the first `20` anchor conditioning records
4. run the current planner / critic stack on those anchors
5. adjust planner and critic for the new taxonomy
