# Round2 Upgrade Brief: pinocchiop

## Goal
Upgrade scaffolded round2 conditioning records from weak to usable or gold without changing their intended mode or track identity.

## Required Fixes

- Add lyric_sources and metadata_sources with confirmed/cross_checked status.
- Upgrade partial lyric grounding to full when possible.
- Fill song_intent.contrast_device.
- Expand section evidence enough to justify ready_for_prompting = true.
- Keep title, likely_mode, and seed direction aligned with the existing scaffold.

## Target Tracks

### pinocchiop_apple_dot_com
- likely_mode: `ironic_meta`
- priority: `high`
- blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing

### pinocchiop_motivation_is_dead
- likely_mode: `ironic_meta`
- priority: `medium`
- blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing

### pinocchiop_nee_nee_nee
- likely_mode: `dark_cute_breakdown`
- priority: `high`
- blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing

### pinocchiop_suki_na_koto_dake_de_ii_desu
- likely_mode: `ironic_meta`
- priority: `high`
- blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
