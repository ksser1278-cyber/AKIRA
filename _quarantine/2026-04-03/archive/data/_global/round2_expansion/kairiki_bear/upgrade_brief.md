# Round2 Upgrade Brief: kairiki_bear

## Goal
Upgrade scaffolded round2 conditioning records from weak to usable or gold without changing their intended mode or track identity.

## Required Fixes

- Add lyric_sources and metadata_sources with confirmed/cross_checked status.
- Upgrade partial lyric grounding to full when possible.
- Fill song_intent.contrast_device.
- Expand section evidence enough to justify ready_for_prompting = true.
- Keep title, likely_mode, and seed direction aligned with the existing scaffold.

## Target Tracks

### kairiki_bear_angel
- likely_mode: `dark_cute_breakdown`
- priority: `high`
- blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing

### kairiki_bear_alkali_rettoushou
- likely_mode: `ironic_meta`
- priority: `medium`
- blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing

### kairiki_bear_lemmingming
- likely_mode: `dark_cute_breakdown`
- priority: `medium`
- blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing

### kairiki_bear_shippaisaku_shoujo
- likely_mode: `direct_emotional_pop`
- priority: `high`
- blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
