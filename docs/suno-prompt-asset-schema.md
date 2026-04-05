# AKIRA Suno Prompt Asset Schema v1

## Purpose

AKIRA needs a prompt-ready layer that sits after metadata and technique extraction.

This layer should not preserve raw source detail.
It should package reusable generation control for Suno-style music prompting.

## Target Output

A `suno_prompt_asset` should contain:

- a short concept line
- a detailed style prompt
- a compact backup tag prompt
- lyric-side guidance
- sound-side guidance
- negative prompt anchors
- optional slider guidance

## Design Rule

Each field should be directly useful in generation.

If a field exists only because it is interesting to archive, it belongs in an earlier layer.

## Required Prompt Families

### 1. Identity

Required:

- `asset_id`
- `track_id`
- `artist_id`
- `mode_id`

### 2. Concept Layer

Required:

- `concept_line`
- `mood_core`
- `story_core`

This is the shortest reusable summary of the track intent.

### 3. Sound Prompt Layer

Required:

- `style_prompt_detailed`
- `style_prompt_compact`
- `genre_anchors`
- `tempo_anchors`
- `arrangement_anchors`
- `production_anchors`
- `vocal_anchors`

### 4. Lyric Prompt Layer

Required:

- `lyric_language_hint`
- `hook_behavior_hint`
- `section_arc_hint`
- `imagery_hint`
- `surface_hint`

### 5. Negative Control Layer

Required:

- `exclude_styles`
- `negative_sound_anchors`
- `negative_lyric_anchors`

### 6. Optional Generation Controls

Recommended:

- `slider_guidance`
- `persona_reuse_hint`
- `edit_strategy_hint`
- `inspire_pool_hint`

## Mapping Rule

The prompt asset should be derived from:

- `vocaloid_metadata_record`
- `lyric_technique_record`
- `track_generation_record`

It should not require raw source lookup at export time.

## Minimum Quality Bar

A usable `suno_prompt_asset` must contain:

- enough sound detail to avoid generic genre prompting
- enough lyric detail to preserve hook and section behavior
- enough negative guidance to block obvious drift

If it cannot do those three things, it is not ready for generation use.
