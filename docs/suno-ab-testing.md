# Suno A/B Testing

This workflow exists to answer a simple question:

`Which style prompt variant actually sounds better inside Suno?`

## What It Tests

The current default pack compares:

- Variant A: `balanced_detailed`
- Variant B: `minimal_core`

Everything else should stay as constant as possible.

## Why This Matters

AKIRA ENGINE now has a stronger style-content layer, but prompt quality still needs real listening tests.
The most useful comparison is not abstract scoring. It is:

- same lyric
- same mode target
- same excludes
- same slider intent
- different style prompt strategy

## Build A/B Packs

For scored Suno-ready song bundles:

```powershell
python build_suno_ab_test_pack.py `
  --source-dir outputs/suno_song_bundle/ado_promptclean88/json `
  --output-dir outputs/suno_ab_packs/ado_promptclean88
```

For mode probes:

```powershell
python build_suno_ab_test_pack.py `
  --source-dir outputs/style_prompt_probes/ado/json `
  --output-dir outputs/suno_ab_packs/ado_mode_probes
```

## Output Files

Each A/B pack contains:

- `suno_ab_test_manifest.json`
- `runbook.md`
- `results_template.jsonl`
- `scorecards/<pair_id>.md`

## Recommended Listening Method

1. Run Variant A and Variant B as close together as possible.
2. Keep lyrics, excludes, and sliders fixed.
3. If one run glitches badly, rerun both variants once.
4. Score both before moving to the next pair.

## Scoring Dimensions

- `voice_fit`
- `arrangement_fit`
- `chorus_lift`
- `emotional_arc`
- `lyric_naturalness`
- `overall`

Also record:

- `preference_rank`
- `suno_url`
- `notes`

## Practical Use

This turns Suno testing into a loop the project can actually learn from:

- generate content atoms
- build prompt variants
- run Suno
- log what won
- revise atoms instead of guessing blindly
