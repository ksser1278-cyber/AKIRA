# AKIRA Supervised Training Schema v1

## Purpose

This document defines the dataset contract for supervised lyric-generation training.

The goal is not to dump raw lyrics into a model. The goal is to teach:

- how section blueprints map to lyric outcomes
- how artist/mode constraints change vocabulary and hook behavior
- how line shape, repetition, and release behavior work in Japanese lyrics

This schema sits **after** corpus ingestion and **after** derived training record generation.

Use the existing intermediate layer first:

- [training-data-shaping.md](/C:/JPop_Songwriter/AKIRA%20ENGINE/docs/training-data-shaping.md)
- [derived_training_record.schema.json](/C:/JPop_Songwriter/AKIRA%20ENGINE/schemas/derived_training_record.schema.json)

Then export only eligible records into the supervised training sample format defined here.

## Dataset Layers

### 1. Reference Corpus

Use for:

- raw lyric source retention
- provenance
- corpus audit
- dossier generation

Do not use directly for supervised tuning.

### 2. Derived Training Records

Use for:

- normalized task shaping
- copyright filtering
- task decomposition
- intermediate QA

This is the current AKIRA intermediate layer.

### 3. Supervised Training Samples

Use for:

- Vertex AI supervised tuning
- task-level model training
- task-level evaluation

This layer is the final export target for model training.

## Core Rules

1. Do not train on raw unstructured lyric dumps.
2. Do not mix benchmark/reference storage with train-ready samples.
3. Do not emit a supervised sample unless rights status is explicitly known.
4. Do not let train and eval share the same track.
5. Do not use artist labels alone as the task instruction.
6. Prefer structured JSON input over long natural-language prompt prose.

## Recommended Task Types

Start with narrow tasks before full-song generation.

- `hook_generation`
- `section_generation`
- `chorus_rewrite`
- `final_release_rewrite`
- `full_song_generation`

Recommended rollout order:

1. `hook_generation`
2. `section_generation`
3. `chorus_rewrite`
4. `final_release_rewrite`
5. `full_song_generation`

## Supervised Sample Contract

Each JSONL row should follow this shape:

```json
{
  "sample_id": "kanaria_king_hook_generation_v1",
  "schema_version": "1.0",
  "split": "train",
  "task": "hook_generation",
  "input": {
    "artist_id": "kanaria",
    "mode_id": "ironic_meta",
    "language": "ja",
    "title_seed": "KING",
    "theme_axes": ["power", "isolation", "arrogance"],
    "blueprint": {
      "sections": [
        {"section": "chorus", "line_target": 4}
      ],
      "hook_constraints": {
        "title_binding": "high",
        "repetition_pressure": "medium",
        "hook_line_target": 2
      }
    },
    "style_constraints": {
      "imagery_atoms": ["玉座", "視線", "支配", "沈黙"],
      "forbidden_generic_atoms": ["夢", "未来", "光"],
      "surface_rules": ["japanese_only", "no_meta_commentary"]
    },
    "phonetic_constraints": {
      "short_line_ratio_target": 0.5,
      "open_vowel_release": true
    }
  },
  "output": {
    "title": "KING",
    "lyrics_markdown": "[chorus]\n..."
  },
  "metadata": {
    "source_track_id": "kanaria_king",
    "source_artist_id": "kanaria",
    "source_tier": "generation_safe",
    "rights_status": "cleared_for_training"
  }
}
```

## Required Top-Level Fields

- `sample_id`
- `schema_version`
- `split`
- `task`
- `input`
- `output`
- `metadata`

## Input Contract

### Required Input Fields

- `artist_id`
- `mode_id`
- `language`
- `blueprint.sections`
- `blueprint.hook_constraints`
- `style_constraints.surface_rules`

### Strongly Recommended Input Fields

- `title_seed`
- `theme_axes`
- `style_constraints.imagery_atoms`
- `style_constraints.forbidden_generic_atoms`
- `phonetic_constraints`

### Input Design Notes

- `input` should describe constraints and structure, not hidden source provenance.
- `input` should not contain raw reference-track commentary or benchmark labels.
- `input` should stay compact and machine-stable.

## Output Contract

### Required Output Fields

- `title`
- `lyrics_markdown`

### Output Rules

- `lyrics_markdown` must use AKIRA section headers such as:
  - `[verse_1]`
  - `[pre_chorus]`
  - `[chorus]`
  - `[bridge]`
  - `[chorus_final]`
- output must stay in Japanese unless the task explicitly allows bilingual content
- no meta commentary
- no analysis notes

## Metadata Contract

### Required Metadata Fields

- `source_track_id`
- `source_artist_id`
- `source_tier`
- `rights_status`

### Recommended Metadata Fields

- `source_mode_id`
- `task_origin`
- `contains_verbatim_lyrics`
- `normalization_version`
- `export_batch_id`

## Rights Policy

Supervised training samples must carry explicit rights gating.

Allowed example values:

- `cleared_for_training`
- `licensed_for_training`
- `internal_only_holdout`
- `not_cleared`
- `unknown`

Rules:

- `not_cleared` and `unknown` must not be exported to the supervised tuning dataset
- `internal_only_holdout` may appear in eval-only workflows, not training
- if a sample contains verbatim commercial lyrics, the rights state must be stricter, not looser

## Split Policy

Use sample splits that prevent leakage.

### Required Rules

1. No identical track in both train and eval.
2. Full-song samples from one track must not be split across train and eval.
3. Rewrite tasks derived from the same exact output target should stay in one split family.
4. Hold out artist-mode combinations when testing generalization, not only random tracks.

### Recommended Split Families

- `train`
- `eval`
- `test`
- `holdout_artist`
- `holdout_mode`

## What To Export

Export only records that satisfy all of:

- structurally normalized
- task-compatible
- rights-gated
- mode-stable enough for the task
- surface-clean enough for the output target

## What Not To Export

Do not export:

- raw scraped lyrics with no task structure
- records with unresolved mode drift
- records with placeholder prose
- records with scaffold/meta contamination
- records with unknown rights status
- records whose output target still depends on analyst free-form notes

## Recommended Build Pipeline

1. ingest source corpus
2. normalize and audit corpus
3. build derived training records
4. filter by rights and quality
5. decompose into supervised tasks
6. export supervised JSONL
7. build eval and holdout manifests
8. run format and leakage validation

## Relationship To Existing AKIRA Layers

Use the current AKIRA dataset path like this:

- corpus and provenance stay in reference records
- shaping and decomposition happen in derived training records
- supervised tuning samples are a new final export layer

This keeps benchmark truth, generation support, and model-training samples from collapsing into one artifact type.

## Current Export Constraint

The current exporter rollout should default to:

- `hook_generation` only

Enable `full_song_generation` only after:

- explicit rights mapping exists
- section alignment is improved
- exported sample validation is in place
