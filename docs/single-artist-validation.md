# Single-Artist Validation

## Goal

Before scaling to multiple artists, confirm that one artist profile already yields meaningful lyric-planning outputs.

## What Counts As Meaningful

A single-artist pipeline is useful when it can do all of the following at the same time:

- stay on the requested theme
- reflect the requested emotion
- preserve mode-specific style tags
- keep structure consistent
- avoid blocked imitation terms
- respond to seed keywords with specific output changes

## Validation Flow

1. Build the artist dataset from `profile.json` and `seeds.json`.
2. Score the resulting records with the single-artist evaluator.
3. Read the markdown report and inspect weak dimensions.
4. Improve the profile, mode definitions, or keyword wiring.
5. Re-run the same seeds to see whether the score improved.

## Command

```powershell
python evaluate_artist.py `
  --artist artists/ado/profile.json `
  --seeds artists/ado/seeds.json
```

## Output

The evaluator writes:

- `reports/<artist_id>_quality_report.md`

## Interpretation Rule

At this stage, a high score means the blueprint pipeline is promising. It does not yet prove that final lyrics or SUNO audio output will be equally strong.
