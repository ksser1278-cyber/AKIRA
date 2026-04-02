# Artist Eval Sets

Once a single-artist package and experiment sets exist, keep the held-out splits separate and turn them into reusable evaluation files.

Example:

```powershell
python build_artist_eval_sets.py `
  --artist-id ado `
  --project-root .
```

Default output:

- `datasets/evals/<artist_id>/mode_selector_eval.jsonl`
- `datasets/evals/<artist_id>/structure_planner_eval.jsonl`
- `datasets/evals/<artist_id>/hook_planner_eval.jsonl`
- `datasets/evals/<artist_id>/style_prompt_eval.jsonl`
- `datasets/evals/<artist_id>/full_song_brief_eval.jsonl`

What each eval record includes:

- held-out input context from the validation or test split
- a compact reference target and reference summary
- a weighted scoring rubric
- safety checks to prevent lyric copying from being rewarded

Why this matters:

- training data tells the model what to imitate
- eval data tells us whether the imitation is actually useful
- keeping Ado-only evals makes it easier to compare prompt formats, planners, or future fine-tunes before scaling out
