# Project Blueprint

## Product Goal

Build a reusable engine that studies Vocaloid / subculture reference styles and converts them into SUNO.AI-ready song packages.

Primary reference axis:

- PinocchioP
- DECO*27

## Core Principle

Treat "artist style" as structured data, not just raw notes.

That gives the project a stable path:

1. Research an artist.
2. Convert the findings into a normalized profile.
3. Generate prompts, lyric plans, and evaluation rules from that profile.
4. Reuse the resulting corpus for model training later.

## Recommended System Layers

### 1. Knowledge Layer

Purpose: store artist traits in a format both humans and scripts can use.

Inputs:

- vocal traits
- style tags
- tempo ranges
- recurring themes
- imagery banks
- forbidden terms
- structure defaults
- mode-specific variations

Suggested storage:

- `artists/<artist_id>/profile.json`
- `artists/_template/subculture_mode_profile.template.json`

### 2. Generation Layer

Purpose: build SUNO-ready outputs from structured artist knowledge.

Outputs:

- style prompt tags
- title ideas
- lyric concept
- section-by-section blueprint
- hook ideas
- generation notes
- final SUNO-ready song package

Current implementation:

- `generate_prompt_package.py`

### 3. Evaluation Layer

Purpose: score whether a generated result still feels aligned with the target profile.

Examples:

- does the tempo sit inside the target mode range
- does the lyric theme match allowed themes
- are forbidden terms excluded
- does the structure follow the intended chorus intensity arc
- are the vocal and sonic descriptors consistent with the chosen mode

### 4. Training Layer

Purpose: prepare future data products for retrieval or fine-tuning.

Possible exports:

- profile-to-package pairs
- theme-to-lyrics pairs
- section prompts and responses
- evaluation labels

## Current Engineering Boundary

The internal engine should own:

- structured conditioning data
- section planning
- style prompt construction
- critic / rerank / benchmark

The internal engine should not be treated as the final sentence-level lyric writer.

For high-quality lyrics, the practical path is:

- internal planner
- external sentence generator
- internal critic / rerank

## Suggested Near-Term Roadmap

### Phase 1

- define the Vocaloid / subculture mode taxonomy
- scaffold PinocchioP and DECO*27 anchor workspaces
- normalize 20 anchor conditioning records
- generate SUNO packages for each core mode

### Phase 2

- compare outputs across `ironic_meta`, `direct_emotional_pop`, and `dark_cute_breakdown`
- improve planner and critic against the 20-track benchmark
- validate external lyric generation roundtrips

### Phase 3

- build a reusable benchmark set for other subculture producers
- add retrieval over reference conditioning records
- evaluate whether fine-tuning is now justified
