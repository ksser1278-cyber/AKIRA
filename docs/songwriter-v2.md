# Songwriter V2

Use this when the old lyric draft renderer is no longer enough and you want a stage-by-stage generation package instead of a single opaque output.

What it produces:

- a structured `plan.json`
- an LLM-ready `prompt_package.json`
- multiple lyric candidates
- critic scores for each candidate
- a selected best draft plus a markdown run report

Example:

```powershell
python run_songwriter_v2.py `
  --source-jsonl datasets/experiments/ado/full_song_brief.jsonl `
  --track-id utaten_hw22011303 `
  --candidate-count 6
```

Default output:

- `outputs/songwriter_v2/<artist_id>/<track_id>/plan.json`
- `outputs/songwriter_v2/<artist_id>/<track_id>/prompt_package.json`
- `outputs/songwriter_v2/<artist_id>/<track_id>/candidate_*.md`
- `outputs/songwriter_v2/<artist_id>/<track_id>/selected_lyric.md`
- `outputs/songwriter_v2/<artist_id>/<track_id>/run_report.md`

Why this exists:

- it makes the corpus useful for generation control instead of only analysis
- it separates planning, prompting, drafting, and critique
- it gives you a clean handoff point for a stronger external model later
