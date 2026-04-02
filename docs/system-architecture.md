# System Architecture

## System Goal

AKIRA ENGINE should behave as a structured songwriting system, not a loose pile of scripts.

The canonical product path is:

1. `conditioning`
2. `planner`
3. `generation`
4. `critic`
5. `bundle`

Everything in the repository should map to one of those layers.

## Layer Map

### 1. Conditioning Layer

Purpose:

- store reusable high-signal anchor records
- encode song intent, section roles, hook logic, Japanese lyric features, and prompt atoms

Canonical locations:

- `data/reference_tracks/<artist_id>/`
- `schemas/track_conditioning_record.schema.json`
- `docs/track-conditioning-records.md`

Inputs:

- lyrics
- credits
- release metadata
- section map
- hook lines
- style notes

Outputs:

- `*.conditioning.json`

### 2. Planner Layer

Purpose:

- convert conditioning records into generation-ready song plans

Canonical locations:

- `datasets/experiments/<artist_id>/full_song_brief.jsonl`
- `scripts/pipeline/build_conditioning_brief_dataset.py`
- `src/akira_engine/songwriter_v2.py`

Inputs:

- conditioning records
- artist mode profiles
- structure profiles

Outputs:

- plan
- prompt package
- candidate generation requests

### 3. Generation Layer

Purpose:

- produce lyric candidates from a plan

Current policy:

- internal rule-based rendering is a fallback and benchmark aid
- external generation is the intended main path

Canonical locations:

- `scripts/songwriter/run_songwriter_v2.py`
- `scripts/songwriter/run_song_package_pipeline.py`
- `src/akira_engine/gemini_songwriter.py`
- `src/akira_engine/songwriter_v2_exchange.py`

Outputs:

- candidate markdown files
- imported external predictions

### 4. Critic Layer

Purpose:

- score candidate quality against plan, motifs, Japanese lyric constraints, and mode behavior

Canonical locations:

- `src/akira_engine/songwriter_v2_scoring.py`
- `scripts/eval/`
- `outputs/*/run_report.md`

Outputs:

- candidate scores
- benchmark reports
- rerank decisions

### 5. Bundle Layer

Purpose:

- emit SUNO-ready packages

Canonical locations:

- `src/akira_engine/suno_package.py`
- `scripts/suno/build_suno_song_bundle.py`
- `outputs/song_package_pipeline/.../suno_bundle/`

Outputs:

- style prompt
- exclude prompt
- final lyric
- bundle manifest

## Directory Contract

### Source of Truth

- `artists/` = artist and mode definitions
- `data/reference_tracks/` = anchor truth
- `datasets/experiments/` = planner-ready inputs
- `src/akira_engine/` = reusable engine code

### Execution Zones

- `scripts/pipeline/` = build truth and planner inputs
- `scripts/songwriter/` = generate or benchmark
- `scripts/eval/` = score and validate
- `scripts/suno/` = package for SUNO

### Output Zones

- `outputs/<domain or artist>/...` = current active runs
- `outputs/_archive/...` = frozen historical comparisons
- `reports/` = human-readable summaries, not source-of-truth machine inputs

## What Is Legacy

The repository still contains legacy or transitional assets.

Treat these as non-canonical unless explicitly needed:

- old Ado-only tuning outputs
- one-off benchmark markdown files stored without a manifest summary
- report-only exports used before conditioning records existed
- ingestion scripts for paths no longer used in the Vocaloid/Subculture line

Do not use those as the default path for new work.

## Canonical Workflows

### New Artist / Producer Onboarding

1. create `artists/<artist_id>/`
2. create anchor set in `data/reference_tracks/<artist_id>/`
3. validate `*.conditioning.json`
4. build `datasets/experiments/<artist_id>/full_song_brief.jsonl`
5. run benchmark matrix
6. tune mode banks or critic only if the benchmark exposes a general rule

### Production Song Package Flow

1. choose artist and conditioning track
2. build planner inputs
3. run `run_song_package_pipeline.py`
4. score imported predictions
5. emit SUNO bundle only if score clears threshold

## Current Engineering Rule

Do not solve quality problems by adding more track-specific branches unless the rule can be generalized into:

- a mode-level section bank
- a planner rule
- a critic rule
- a conditioning extraction rule

If a fix cannot be generalized, it should not be the default path.
