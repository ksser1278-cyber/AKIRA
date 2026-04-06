# AKIRA Wiki Layer

AKIRA now uses a persistent wiki layer between raw sources and downstream generation assets.

This layer follows the same pattern:

- raw sources
- wiki
- schema

## Purpose

The wiki is the persistent knowledge artifact for AKIRA.

It is not the raw source of truth and it is not the final training JSONL.
It is the maintained synthesis layer where track, producer, voicebank, mode, hook, and sound knowledge accumulates over time.

## Layer Mapping

### Raw sources

- VocaDB metadata
- Vocaloid Wiki metadata
- official upload links
- trusted lyric sources
- rights evidence
- canonical metadata JSON
- lyric grounding bundles

These are immutable or near-immutable reference inputs.

### Wiki

The wiki is a markdown knowledge base under `wiki/`.

It contains:

- track pages
- producer pages
- voicebank pages
- mode pages
- technique pages
- sound pages
- overview pages
- source summaries
- contradiction and patch notes
- index and log

### Schema

The schema is the set of rules and contracts that govern how the wiki is maintained.

Current governing files:

- `README.md`
- `docs/README.md`
- this file
- JSON schemas in `schemas/`

## Directory Contract

The AKIRA wiki root is:

- `C:\JPop_Songwriter\AKIRA ENGINE\wiki`

The minimum structure is:

- `wiki/index.md`
- `wiki/log.md`
- `wiki/overview/`
- `wiki/tracks/`
- `wiki/producers/`
- `wiki/voicebanks/`
- `wiki/modes/`
- `wiki/techniques/`
- `wiki/sound/`
- `wiki/sources/`
- `wiki/patches/`

## Page Types

### Track pages

One page per canonical `track_id`.

Contains:

- title
- producer
- voicebank
- canonical source links
- lyric technique summary
- sound profile summary
- generation readiness summary
- prompt-asset relevance
- links to related producer, mode, and technique pages

### Producer pages

Contains:

- producer summary
- recurring lyric devices
- recurring sound markers
- canonical track list
- style lineage notes

### Voicebank pages

Contains:

- voicebank identity
- typical sound framing
- common emotional and diction usage
- linked producers and tracks

### Mode pages

Contains:

- mode definition
- lyric behavior patterns
- sound behavior patterns
- representative tracks

### Technique pages

Contains:

- hook devices
- section behaviors
- imagery systems
- diction patterns
- narrative stance patterns

### Sound pages

Contains:

- texture clusters
- arrangement behaviors
- energy arcs
- producer-specific sound anchors

## Special Files

### `index.md`

Content-oriented directory of the wiki.

It should list:

- major sections
- important pages
- one-line summary per page

### `log.md`

Append-only chronological log.

Use stable headings:

- `## [YYYY-MM-DD] ingest | ...`
- `## [YYYY-MM-DD] wiki-update | ...`
- `## [YYYY-MM-DD] patch | ...`
- `## [YYYY-MM-DD] readiness | ...`

## Operating Rule

Raw data is not queried directly unless necessary.

The intended flow is:

1. ingest raw source
2. update canonical metadata
3. update wiki pages
4. derive generation records / prompt assets / training records

## Current Execution Focus

The first useful AKIRA wiki should be generated from:

- `vocaloid_metadata_canonical/tier1_map_seed`
- Tier1 grounded lyric technique imports
- Tier1 generation readiness and prompt asset outputs

This gives a compact but already connected knowledge base.
