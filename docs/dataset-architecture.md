# Dataset Architecture

## Goal

Separate high-trust benchmark data from broader support data so engine tuning does not overfit to a tiny anchor set or get diluted by noisy expansion records.

## Layers

### 1. Gold Anchor Set

- Path: `C:\JPop_Songwriter\AKIRA ENGINE\data\anchor_sets\gold_anchor_set.json`
- Purpose: benchmark, critic calibration, demos, regression
- Rule: keep this set small and stable

### 2. Producer Expansion Set

- Path: `C:\JPop_Songwriter\AKIRA ENGINE\data\anchor_sets\producer_expansion_set.json`
- Purpose: broaden a producer line after the anchor set is stable
- Rule: records can be `usable`; they do not need to be audio-aligned

### 3. Mode Support Set

- Path: `C:\JPop_Songwriter\AKIRA ENGINE\data\anchor_sets\mode_support_set.json`
- Purpose: generalize mode logic across producers
- Rule: add records only after anchor and producer expansion are stable

### 4. Audio-Aligned Set

- Path: `C:\JPop_Songwriter\AKIRA ENGINE\data\anchor_sets\deco27_audio_aligned_anchor_set.json`
- Related audio map: `C:\JPop_Songwriter\AKIRA ENGINE\data\audio_manifest.json`
- Purpose: factual sound enrichment and sound-proxy validation
- Rule: audio-aligned records must map cleanly to `audio_manifest.json`

### 5. Prompt Validation Set

- Path: `C:\JPop_Songwriter\AKIRA ENGINE\data\anchor_sets\prompt_validation_set.json`
- Purpose: fixed prompt-generation test cases
- Rule: keep this set frozen unless a case is intentionally replaced

## Operating Rules

1. Tune against `gold_anchor` and `prompt_validation`.
2. Check drift against `producer_expansion`.
3. Add `mode_support` only to improve generalization, not to repair a single hard case.
4. Use `audio_aligned` only for claims that require owned-audio evidence.
5. Never collapse all records into one benchmark source.

## Current Practical Use

- `pinocchiop` and `deco27` active anchor tracks live in `gold_anchor_set.json`.
- Additional PinocchioP pending tracks and legacy DECO*27 reference tracks live in `producer_expansion_set.json`.
- Audio-backed DECO*27 active tracks remain listed in `deco27_audio_aligned_anchor_set.json`.
