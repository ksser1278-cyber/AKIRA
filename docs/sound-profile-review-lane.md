# Sound Profile Review Lane

## Purpose

The current joined tracks can already reach `production_candidate`.

They do not reach `professional_target` because the sound layer is still inferred at `partial` quality.

This lane exists to upgrade sound profile quality from `partial` to `reviewed`.

## Immediate Input Set

Start with the first joined Tier 1 subset:

- `tier1_map_seed_pilot10_v2`
- `tier1_map_seed_pilot10_merged_v10`

## Upgrade Goal

For each reviewed track, resolve at least:

- tempo feel
- energy arc label
- chorus lift strategy
- arrangement density profile
- instrumentation core
- texture markers
- vocal performance character
- safe positive sound anchors
- negative sound anchors

## Quality Effect

When a joined track has:

- lyric technique quality = `reviewed`
- sound profile quality = `reviewed`
- sufficient lyric and sound signal density

it can move from `production_candidate` toward `professional_target`.

## Order Of Work

1. keep lyric grounding expansion moving
2. review sound profile on the existing joined subset
3. rerun generation-readiness audit
4. use the reviewed subset as the first professional-target candidate lane

## Workspace Rule

Sound review should run through a separate workspace instead of direct record edits.

Current commands:

```powershell
python akira.py dataset build-sound-profile-review-workspace --project-root . --generation-root datasets\training\generation_profiles\tier1_map_seed_pilot10_merged_v10 --corpus-root datasets\_global\vocaloid_metadata_canonical\tier1_map_seed --output-root datasets\_global\sound_profile_review\tier1_map_seed_pilot10_v1
python akira.py dataset import-reviewed-sound-profiles --project-root . --generation-root datasets\training\generation_profiles\tier1_map_seed_pilot10_merged_v10 --workspace-root datasets\_global\sound_profile_review\tier1_map_seed_pilot10_v1 --output-root datasets\training\generation_profiles\tier1_map_seed_pilot10_sound_reviewed_v1
```

`incoming/` holds review templates.
Only `accepted/` records are allowed to upgrade `sound_profile_quality` to `reviewed`.
