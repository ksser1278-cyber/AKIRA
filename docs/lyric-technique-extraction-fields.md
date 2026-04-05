# AKIRA Lyric Technique Extraction Fields v1

## Purpose

The target is not to train on raw lyric dumps.

The target is to learn reusable songwriting technique from a very large lyric corpus.

This document defines the extraction layer that sits between:

1. `reference_corpus`
2. `derived_training_record`
3. `supervised_training_sample`

If AKIRA is meant to learn from tens of thousands of songs, this layer is the core contract.

## Design Rule

Extract fields that answer:

- how the song is structured
- how the hook is built
- how tension rises and releases
- what imagery bank is active
- what phonetic and line-shape constraints are operating
- what narrative stance the lyric takes

Do not optimize this layer for archival completeness.
Optimize it for controllable generation and training export.

## Layer Relationship

### Reference Corpus

Stores:

- raw lyric text
- provenance
- rights
- audit history

### Technique Extraction Record

Stores:

- section behavior
- hook behavior
- emotional movement
- imagery and diction patterns
- phonetic and line-shape behavior
- narrative stance
- reusable constraints

### Derived Training Record

Stores:

- task-shaped planning targets
- generation-safe intermediate structure

### Supervised Training Sample

Stores:

- model-ready task input/output examples

## Required Extraction Field Families

### 1. Track Identity

Required:

- `track_id`
- `artist_id`
- `title`
- `language`

### 2. Source Integrity

Required:

- `rights_status`
- `lyric_source_quality`
- `section_alignment_status`
- `text_cleanliness_status`

This layer determines whether the track can move downstream at all.

### 3. Structural Blueprint

Required:

- `ordered_sections`
- `section_count`
- `has_pre_chorus`
- `has_bridge`
- `has_outro`
- `chorus_anchor_sections`
- `form_confidence`

Per-section recommended fields:

- `section_label`
- `normalized_role`
- `line_count`
- `relative_position`
- `entry_energy`
- `exit_energy`
- `function`

### 4. Hook Construction

Required:

- `hook_lines`
- `hook_candidate_count`
- `hook_density`
- `title_binding_strength`
- `repetition_profile`
- `chorus_repetition_score`

This family should answer how the chorus locks attention.

### 5. Emotional Arc

Required:

- `overall_arc_label`
- `section_emotion_flow`
- `peak_section`
- `release_section`
- `valence_trend`
- `intensity_trend`

### 6. Imagery and Motif Bank

Required:

- `imagery_tags`
- `motif_clusters`
- `object_bank`
- `body_reference_level`
- `space_reference_level`
- `digital_reference_level`

This family captures reusable symbolic material without requiring verbatim reuse.

### 7. Diction and Surface

Required:

- `register`
- `directness_level`
- `abstraction_level`
- `english_insertion_level`
- `slang_level`
- `imperative_usage_level`

### 8. Narrative Stance

Required:

- `dominant_perspective`
- `address_target`
- `narrative_distance`
- `confession_vs_performance`
- `irony_level`

### 9. Phonetic and Line-Shape Profile

Required:

- `line_length_profile`
- `short_line_ratio`
- `long_line_ratio`
- `syllabic_density_band`
- `terminal_sound_profile`
- `open_vowel_release_rate`

This is the mechanics layer that helps the engine learn singable Japanese line behavior.

### 10. Contrast and Twist Devices

Recommended:

- `pivot_lines`
- `contrast_device_count`
- `twist_presence`
- `contrast_device_labels`

### 11. Mode Evidence

Required:

- `candidate_modes`
- `mode_evidence_notes`
- `mode_confidence`

Important rule:

This family stores evidence for later internal labeling.
It should not force an unstable final mode assignment too early.

### 12. Task Eligibility

Required:

- `eligible_tasks`
- `blocked_tasks`
- `blocking_reasons`

This family decides what the track can safely support later:

- `hook_generation`
- `section_generation`
- `chorus_rewrite`
- `final_release_rewrite`
- `full_song_generation`

## Minimum Extraction Outcome

A usable extraction record must answer:

- what the chorus is doing
- how repetition is being used
- how energy rises and resolves
- what imagery bank is active
- what line-shape constraints are visible
- what downstream tasks the track can support

If it cannot answer those, it is not yet a usable technique record.

## What This Enables

At scale, this layer allows AKIRA to:

- retrieve technique without memorizing songs
- build supervised tasks from evidence instead of guesses
- compare artist families by mechanism rather than surface similarity
- audit corpus diversity before paying training cost

## Recommended Build Order

For the long-term tens-of-thousands-song goal:

1. build `reference_corpus`
2. extract `lyric_technique_record`
3. convert into `derived_training_record`
4. export `akira_supervised_training_sample`

Do not invert this order.
