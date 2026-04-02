# Dataset Pipeline

## Immediate Goal

Build a dataset that helps a lyric-generation system learn how to plan songs before it learns how to write full lyrics.

This stage is downstream from lyric ingestion and normalization.

This project stage focuses on:

- structured artist profiles
- scenario seed records
- training-ready blueprint examples in JSONL

## Why Blueprint Data First

Full commercial lyrics create both quality and rights problems. Blueprint data is a safer and more controllable foundation.

The dataset generated here contains:

- prompt instructions
- artist and mode constraints
- theme and narrative inputs
- target outputs such as style tags, hook ideas, and section goals

The dataset intentionally does not store scraped commercial lyrics.

## Pipeline Shape

### 1. Research

Capture artist traits as notes and references.

Current source:

- `data/`

### 2. Normalize

Convert the research into structured profiles.

Current source:

- `artists/<artist_id>/profile.json`

### 3. Seed

Prepare scenario records that represent the kinds of songs we want the system to plan.

Current source:

- `artists/<artist_id>/seeds.json`

### 4. Build Dataset

Combine the profile and the seed file into JSONL training records.

Current output:

- `datasets/processed/<artist_id>_lyric_blueprints.jsonl`

## Record Design

Each dataset record contains:

- an instruction for the future lyric-planning model
- structured input context
- a target blueprint
- safety notes

This makes the dataset useful for:

- supervised fine-tuning later
- retrieval-augmented generation
- prompt templating
- internal QA and evaluation

## Commands

Build the Ado lyric blueprint dataset:

```powershell
python build_dataset.py `
  --artist artists/ado/profile.json `
  --seeds artists/ado/seeds.json
```

Build every artist dataset found under `artists/`:

```powershell
python build_all_datasets.py
```

Merge per-artist datasets into one training corpus:

```powershell
python build_corpus.py
```

Evaluate whether one artist already produces meaningful blueprint quality:

```powershell
python evaluate_artist.py `
  --artist artists/ado/profile.json `
  --seeds artists/ado/seeds.json
```

Generate a single markdown prompt package for inspection:

```powershell
python generate_prompt_package.py `
  --artist artists/ado/profile.json `
  --mode rock_rebellion `
  --theme "pressure and rebellion" `
  --emotion "defiant" `
  --narrative "A masked narrator breaks out of social pressure at midnight."
```

## Recommended Next Step

Once 3 to 5 artists have profiles and seed sets in the same format, the next best move is to add a lyric expander that converts blueprint records into section-level draft lyrics.

## Scaling Rule

When adding a new artist:

1. Copy `artists/_template/profile.template.json` to `artists/<artist_id>/profile.json`.
2. Copy `artists/_template/seeds.template.json` to `artists/<artist_id>/seeds.json`.
3. Fill in the profile and seed records.
4. Run `python build_all_datasets.py`.
5. Run `python build_corpus.py`.
