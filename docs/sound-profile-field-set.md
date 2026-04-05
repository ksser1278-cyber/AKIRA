# AKIRA Sound Profile Field Set v1

## Purpose

AKIRA should not collect song information only for lyric analysis.

The corpus also needs a reusable sound-intelligence layer that can support:

1. generation control
2. Suno prompt packaging
3. producer sound-family comparison
4. later training or retrieval over arrangement and production behavior

This document defines the minimum sound-side field families that should exist before large-scale prompt packaging begins.

## Design Rule

Store fields that help answer:

- what the track feels like in motion
- how the arrangement is staged
- what production textures dominate
- where energy lifts and drops occur
- what performance character the synthetic vocal implies

Do not optimize this layer for musicological completeness.
Optimize it for controllable music generation.

## Required Field Families

### 1. Tempo and Meter

Required:

- `bpm_estimate`
- `tempo_band`
- `tempo_feel`
- `meter_signature`
- `swing_or_straight`

### 2. Energy Curve

Required:

- `global_energy_level`
- `energy_arc_label`
- `section_energy_map`
- `peak_section`
- `release_section`
- `drop_presence`

### 3. Groove Profile

Required:

- `groove_family`
- `rhythmic_drive`
- `syncopation_level`
- `kick_pattern_density`
- `snare_behavior`
- `subdivision_feel`

### 4. Arrangement Core

Required:

- `intro_behavior`
- `verse_arrangement_density`
- `chorus_lift_strategy`
- `bridge_behavior`
- `outro_behavior`
- `arrangement_density_profile`

### 5. Instrumentation Core

Required:

- `primary_instruments`
- `secondary_instruments`
- `rhythm_section_presence`
- `lead_element_type`
- `pad_or_atmosphere_type`
- `acoustic_vs_electronic_balance`

### 6. Production Texture

Required:

- `texture_markers`
- `distortion_level`
- `glitch_presence`
- `sidechain_presence`
- `transient_hardness`
- `stereo_width_profile`

### 7. Harmonic and Tonal Feel

Recommended:

- `tonal_center_status`
- `mode_feel`
- `harmonic_brightness`
- `tension_density`
- `cadence_behavior`

This family is useful even when exact musical key is unavailable.

### 8. Vocal Performance Character

Required:

- `vocal_presence_style`
- `vocal_intensity`
- `vocal_character_markers`
- `stacking_behavior`
- `call_response_presence`
- `synthetic_voice_emphasis`

This family should describe performance character, not only the name of the voicebank.

### 9. Producer Sound Signatures

Required:

- `producer_sound_markers`
- `genre_hybrid_markers`
- `era_signifiers`
- `reference_scene_markers`

This family allows comparison by mechanism instead of title-level similarity.

### 10. Generation Constraints

Required:

- `prompt_safe_sound_anchors`
- `negative_sound_anchors`
- `sound_confidence`
- `sound_profile_source_basis`

These fields are the direct bridge into prompt packaging.

## Minimum Outcome

A usable sound profile should answer:

- how fast the track moves
- where the lift happens
- what the core arrangement feels like
- what textures dominate
- what vocal-performance character is implied
- what sound anchors are safe to reuse in prompts

If a record cannot answer those, it is not yet prompt-ready.

## Future Layer Relationship

Recommended long-term flow:

1. `vocaloid_metadata_record`
2. `lyric_technique_record`
3. `track_generation_record`
4. `suno_prompt_asset`

The sound profile should live inside `track_generation_record`, not as disconnected ad hoc tags.
