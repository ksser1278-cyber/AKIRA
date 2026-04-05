# Round2 Expansion Packet: deco27

## Purpose
This packet is the handoff unit for upgrading round2 scaffold records into fully grounded usable records.

## Queue Summary

- validated `1`
- scaffolded `4`

## Current Queue Snapshot

- `deco27_hibana` / status `validated` / priority `high` / mode `direct_emotional_pop`
- `deco27_mozaik_role` / status `scaffolded` / priority `high` / mode `ironic_meta`
- `deco27_yowamushi_montblanc` / status `scaffolded` / priority `medium` / mode `direct_emotional_pop`
- `deco27_salamander` / status `scaffolded` / priority `high` / mode `ironic_meta`
- `deco27_android_girl` / status `scaffolded` / priority `high` / mode `direct_emotional_pop`

## Current Audit Summary

- Records: `5`
- Gold: `1`
- Usable: `0`
- Weak: `4`
- Average score: `30.2`

## Weak Track Upgrade Targets

### deco27_mozaik_role
- Score: `16`
- full_text_status: `partial`
- trusted_ratio: `0.0`
- hook_lines: `2`
- prompt anchors: `17`
- Blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
- Warnings: lyric text is only partial; quality_control.missing_fields has 3 entries; manual review required for 3 fields; question_lines missing

### deco27_yowamushi_montblanc
- Score: `16`
- full_text_status: `partial`
- trusted_ratio: `0.0`
- hook_lines: `2`
- prompt anchors: `17`
- Blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
- Warnings: lyric text is only partial; quality_control.missing_fields has 3 entries; manual review required for 3 fields; question_lines missing

### deco27_salamander
- Score: `16`
- full_text_status: `partial`
- trusted_ratio: `0.0`
- hook_lines: `2`
- prompt anchors: `17`
- Blockers: song_intent.contrast_device missing or empty; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
- Warnings: lyric text is only partial; quality_control.missing_fields has 3 entries; manual review required for 3 fields; question_lines missing

### deco27_android_girl
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

- `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\round2_seed_scaffolds`

## Validated Tracks

- `deco27_hibana` / score `87` / keep as benchmarked round2 winner

## Incoming Directory

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\round2_expansion\deco27\incoming`
