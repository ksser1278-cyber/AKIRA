# Metadata Source Policy

## Purpose

This document separates:

- song-information gathering
- lyric-text training eligibility

These are not the same source class and should not be mixed.

## Core Rule

Use Vocaloid-specialist databases and wikis for:

- release metadata
- creator credits
- singer or voicebank information
- upload chronology
- version and tie-in context
- interpretation hints for later internal review

Do not treat those same sources as automatic permission for verbatim lyric training use.

## Preferred Metadata Sources

Preferred metadata sources for Vocaloid and adjacent catalog work:

1. official creator, label, or publisher pages
2. official YouTube or NicoNico uploads
3. [VocaDB](https://vocadb.net)
4. Vocaloid-specialist wiki pages such as Vocaloid Wiki or project-specific song databases

For AKIRA, metadata collection should be treated as `Vocaloid-only` unless a separate corpus explicitly targets another synthetic-song ecosystem.

## Usage Scope

### Allowed as metadata or song-intelligence references

- VocaDB
- Vocaloid Wiki
- fandom-style song databases with track-level credits and release context
- official upload pages used for release and creator attribution

### Not sufficient on their own for lyric-training clearance

- VocaDB
- Vocaloid Wiki
- fandom-style lyric or summary pages
- unofficial mirrors

## Operational Rule

When building AKIRA datasets:

- `metadata_sources` may cite Vocaloid-specialist databases and wikis
- `lyric_sources` used for verbatim training text must still satisfy the separate rights-cleared lyric-source policy

## Intake Guidance

If a track package uses a wiki-style source, record it as:

- metadata support
- interpretation support
- mode-verification support

Do not record it as the sole basis for:

- `cleared_for_training`
- `licensed_for_training`
- verbatim lyric ingestion

## Practical Default

For Vocaloid catalog work:

- use VocaDB and Vocaloid Wiki early
- attach them under metadata references
- keep lyric-training approval gated by explicit rights evidence
