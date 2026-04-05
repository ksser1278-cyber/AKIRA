# Low-Value Data Policy

## Purpose

AKIRA should retain lower-value records during the build toward the large corpus target.

But retention without classification creates noise.

This policy defines how lower-value records are identified, retained, and separated from high-priority generation work.

## Core Rule

Lower-value does not mean disposable.

Before the corpus foundation is complete:

- do not delete lower-value records
- do classify them explicitly
- do keep them out of premium lanes unless promoted later

## What Low-Value Means

A record is low-value when it is structurally retained but weak for downstream generation use.

Typical reasons:

1. title quality is weak
2. producer identity is weak
3. vocal identity is weak
4. original upload lineage is weak
5. variant ambiguity is high
6. downstream joinability potential is low

## Value Tiers

### `core`

High-value records suitable for priority downstream work.

Expected traits:
- accepted canonical metadata
- stable producer identity
- stable vocal identity
- official upload lineage present
- no major placeholder corruption

### `supporting`

Useful records that are retained and usable, but not first-choice for premium downstream work.

Typical traits:
- metadata accepted
- minor ambiguity remains
- still valuable for scale, coverage, or future review

### `low_value_retained`

Retained records with limited immediate downstream value.

Typical traits:
- placeholder-like title residue
- weak producer normalization
- missing original upload lineage
- high variant ambiguity
- sparse downstream confidence

### `deferred`

Records worth retaining, but they should not consume premium processing budget yet.

Typical traits:
- major ambiguity
- multiple unresolved weak signals
- likely future patch/review requirement

## Flag Families

Use explicit flags instead of vague judgment.

Recommended flag families:
- `title:*`
- `credits:*`
- `vocal:*`
- `source:*`
- `variant:*`
- `generation:*`

## Operational Rule

Low-value classification affects priority, not existence.

Meaning:
- `core` enters priority lanes first
- `supporting` remains in the main corpus and can be promoted later
- `low_value_retained` stays in the corpus but is deprioritized for premium lanes
- `deferred` stays available but should be isolated from current premium loops

## Deletion Rule

Deletion is not part of the current build-to-foundation phase.

Deletion review happens only after:
- the corpus foundation target is met
- current premium subsets are stable
- there is a clear reason to remove rather than isolate

## Immediate Use

This policy should feed:
- corpus planning
- metadata expansion prioritization
- lyric grounding prioritization
- generation readiness prioritization
