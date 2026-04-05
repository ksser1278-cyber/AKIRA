# Rights-Cleared Training Corpus

## Purpose

This document defines the next dataset track for supervised training after the current UtaTen-derived corpus was conservatively blocked for training use.

The problem is not dataset shape.
The problem is rights.

AKIRA already has:

- a supervised sample schema
- a derived dataset exporter
- a rights map gate

What it does not yet have is a corpus that can be defensibly marked:

- `cleared_for_training`
- or `licensed_for_training`

## Current State

Current reduced-workspace export path works technically:

- `python akira.py dataset build-derived`
- `python akira.py dataset bootstrap-rights`
- `python akira.py dataset export-supervised`

But the current Ado pilot remains blocked because the source basis is UtaTen-hosted lyrics and the reviewed terms do not permit training reuse.

## Rule

Do not try to solve this by weakening the rights gate.

Do not mark scraped lyric sources as trainable unless there is explicit permission, license evidence, or a separately documented internal legal basis.

## Acceptable Corpus Paths

The next training corpus must come from one of these paths:

1. direct license
   - explicit negotiated permission for training use
2. owned or commissioned text
   - original lyric text created for AKIRA
3. training-cleared partner corpus
   - contractually usable for model training
4. internal holdout-only corpus
   - usable for evaluation or retrieval testing only, not training

## Required Metadata For Any New Corpus

Each track-level source record should be able to answer:

- who owns the text
- what permission basis exists
- whether training is allowed
- whether eval-only use is allowed
- where the evidence is stored
- who reviewed it
- when it was reviewed

Song-information references such as VocaDB or Vocaloid Wiki may also be attached for metadata support, but they do not replace lyric-rights evidence.

## Minimum Rights Record Shape

At minimum, each candidate track should carry:

- `track_id`
- `artist_id`
- `rights_status`
- `source_basis`
- `notes`
- `reviewed_at`
- `reviewer`
- `evidence_ref`

Optional but recommended:

- `metadata_references.sources`
- `metadata_references.notes`

Use those fields for:

- release metadata
- creator credit confirmation
- mode-verification support
- interpretation context

Do not use them as the sole basis for lyric-training clearance.

## Recommended Next Pilot

Do not continue the UtaTen Ado set for training.

Instead, open a new pilot with:

- small track count
- one corpus family
- clear permission basis
- hook-generation only

Suggested first target:

- 10 to 30 tracks
- one rights basis
- one task type

Current active recommendation:

- `owned_original`
- `hook_generation`
- start with a tiny seed and expand only after export succeeds

## Operational Rule

For the rebuild workspace:

- dataset shape work may continue
- exporter work may continue
- rights map work may continue
- supervised training must stay blocked until a rights-cleared corpus exists
