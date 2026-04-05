# Round2 Expansion Packet: pinocchiop

## Purpose
This packet is the handoff unit for upgrading round2 scaffold records into fully grounded usable records.

## Queue Summary

- validated `1`
- scaffolded `4`

## Current Queue Snapshot

- `pinocchiop_slow_motion` / status `validated` / priority `high` / mode `ironic_meta`
- `pinocchiop_apple_dot_com` / status `scaffolded` / priority `high` / mode `ironic_meta`
- `pinocchiop_motivation_is_dead` / status `scaffolded` / priority `medium` / mode `ironic_meta`
- `pinocchiop_nee_nee_nee` / status `scaffolded` / priority `high` / mode `dark_cute_breakdown`
- `pinocchiop_suki_na_koto_dake_de_ii_desu` / status `scaffolded` / priority `high` / mode `ironic_meta`

## Current Audit Summary

- Records: `5`
- Gold: `1`
- Usable: `0`
- Weak: `4`
- Average score: `30.2`

## Weak Track Upgrade Targets

### pinocchiop_apple_dot_com
- Score: `16`
- full_text_status: `partial`
- trusted_ratio: `0.0`
- hook_lines: `2`
- prompt anchors: `18`
- Blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
- Warnings: lyric text is only partial; quality_control.missing_fields has 3 entries; manual review required for 3 fields; question_lines missing

### pinocchiop_motivation_is_dead
- Score: `16`
- full_text_status: `partial`
- trusted_ratio: `0.0`
- hook_lines: `2`
- prompt anchors: `17`
- Blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
- Warnings: lyric text is only partial; quality_control.missing_fields has 3 entries; manual review required for 3 fields; question_lines missing

### pinocchiop_nee_nee_nee
- Score: `16`
- full_text_status: `partial`
- trusted_ratio: `0.0`
- hook_lines: `2`
- prompt anchors: `18`
- Blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
- Warnings: lyric text is only partial; quality_control.missing_fields has 3 entries; manual review required for 3 fields; question_lines missing

### pinocchiop_suki_na_koto_dake_de_ii_desu
- Score: `16`
- full_text_status: `partial`
- trusted_ratio: `0.0`
- hook_lines: `2`
- prompt anchors: `17`
- Blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
- Warnings: lyric text is only partial; quality_control.missing_fields has 3 entries; manual review required for 3 fields; question_lines missing

## Required Upgrades

- Add lyric_sources and metadata_sources with confirmed/cross_checked status.
- Upgrade partial lyric grounding to full where possible.
- Fill song_intent.contrast_device.
- Raise quality_control.ready_for_prompting only when grounding is sufficient.
- Keep track_id, likely_mode, and seed direction intact.

## Seed Directory

- `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\round2_seed_scaffolds`

## Validated Tracks

- `pinocchiop_slow_motion` / score `87` / keep as benchmarked round2 winner

## Incoming Directory

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\round2_expansion\pinocchiop\incoming`
