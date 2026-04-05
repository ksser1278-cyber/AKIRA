# Vocaloid Corpus Inclusion Policy

## Purpose

AKIRA's large-scale reference corpus should be explicitly constrained to Vocaloid music and adjacent synthetic-voice song culture.

This policy exists to prevent the metadata and technique corpus from drifting into general J-pop, anime-pop, or creator-pop without a clear Vocaloid connection.

## Inclusion Rule

Include a track only if at least one of the following is true:

1. the original or defining version uses a Vocaloid voicebank
2. the original or defining version uses a closely related synthetic singing stack such as:
   - Synthesizer V
   - CeVIO
   - UTAU
   - VOICEROID song-culture derivatives
3. the track is cataloged by Vocaloid-specialist databases as part of the Vocaloid producer ecosystem and the synthetic-voice version is the canonical release

## Exclusion Rule

Exclude or separately quarantine:

- human-singer originals with no synthetic-voice canonical version
- anime soundtrack material with no Vocaloid-culture grounding
- generic J-pop and internet pop unrelated to the Vocaloid producer ecosystem
- pure cover uploads
- karaoke, instrumental, or stem-only uploads
- remix variants unless the remix is the culturally canonical version
- self-covers by human singers when the synthetic-voice original is the actual reference track

## Track Canonicalization

For each included song, define one canonical track identity:

- canonical title
- canonical producer or creator identity
- canonical synthetic singer or voicebank identity
- canonical original upload or release reference

Non-canonical variants may be attached as references, but they should not create duplicate primary track records.

## Required Metadata Axes

Each accepted metadata record should capture:

- producer
- synthetic singer or voicebank
- original upload platform
- original upload date
- title variants
- release or album tie-ins when relevant
- collaboration or feature credits
- remake or self-cover relationships
- whether the synthetic-voice version is canonical

## Coverage Goal

The goal is not just a large track count.
The goal is a large and balanced Vocaloid corpus.

Track acquisition should maximize spread across:

- producers
- years
- voicebanks
- substyles or modes
- energy levels
- hook structures
- narrative stances

## Source Priority

Use these source classes for metadata collection:

1. official creator or publisher sources
2. official YouTube or NicoNico uploads
3. VocaDB
4. Vocaloid-specialist wiki pages

Use VocaDB and Vocaloid Wiki aggressively for catalog breadth, but treat them as metadata-support sources rather than lyric-training clearance.

## Operational Split

The corpus should remain split into three layers:

- `metadata_corpus`
  - broadest possible Vocaloid catalog
- `technique_corpus`
  - tracks with enough structure and text quality for technique extraction
- `training_corpus`
  - rights-cleared subset only

## Default Decision

When a track is ambiguous:

- include it in neither training nor technique by default
- keep it out until a clear synthetic-voice canonical basis is established
