# Round2 Upgrade Brief: kanaria

## Goal
Upgrade scaffolded round2 conditioning records from weak to usable or gold without changing their intended mode or track identity.

## Required Fixes

- Add lyric_sources and metadata_sources with confirmed/cross_checked status.
- Upgrade partial lyric grounding to full when possible.
- Fill song_intent.contrast_device.
- Expand section evidence enough to justify ready_for_prompting = true.
- Keep title, likely_mode, and seed direction aligned with the existing scaffold.

## Target Tracks

### kanaria_mira
- likely_mode: `direct_emotional_pop`
- priority: `medium`
- blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing

### kanaria_yoidore_shirazu
- likely_mode: `dark_cute_breakdown`
- priority: `high`
- blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing

### kanaria_requiem
- likely_mode: `direct_emotional_pop`
- priority: `medium`
- blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing

### kanaria_daino_tekina_rendezvous
- likely_mode: `ironic_meta`
- priority: `high`
- blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
