# maretu_pink Mode Verification Packet

- target track: `maretu_pink`
- workflow: `mode_verification_only`
- required outcome: decide whether `song_intent.narrative_role` can be set to exactly one supported mode

## Read First

- `C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\generation_safety_maretu_pink_mode_verification.md`
- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\generation_safety_remaining_source_acquisition\maretu\packet.md`
- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\generation_safety_remaining_source_acquisition\maretu\incoming\maretu_pink.json`
- `C:\JPop_Songwriter\AKIRA ENGINE\artists\maretu\profile.json`
- `C:\JPop_Songwriter\AKIRA ENGINE\artists\maretu\representative_demo_profile.json`

## Editable Scope

- `song_intent.narrative_role`
- `source_provenance.notes`

## Do Not Edit

- `lyric_ground_truth.sections`
- `lyric_ground_truth.hook_lines`
- `source_provenance.lyric_sources`
- `source_provenance.metadata_sources`
- any engine code

## Success Gate

- one supported mode only
- no new provenance claims without source support
- no lyric rewrite
- no speculative second mode
