# Lyric Draft Generation

Use the derived brief records to render a readable original lyric draft.

Important:

- this step uses only abstracted corpus features
- it avoids direct imitation of any living artist
- it does not reuse scraped lyrics

Example:

```powershell
python generate_lyric_draft.py `
  --source-jsonl datasets/evals/ado/full_song_brief_eval.jsonl `
  --track-id utaten_hw22011303
```

Default output:

- `outputs/lyric_drafts/<artist_id>/<track_id>.md`

Good sources to feed in:

- `datasets/evals/<artist_id>/full_song_brief_eval.jsonl`
- `datasets/experiments/<artist_id>/full_song_brief.jsonl`
