# Lyric Draft Batch Test

Use this when you want more than one or two sample songs and need a quick read on whether the draft generator is following the brief design.

Example:

```powershell
python run_lyric_draft_batch_test.py `
  --source-jsonl datasets/experiments/ado/full_song_brief.jsonl `
  --count 28
```

What it does:

- selects a diverse subset of records
- skips track ids that already have draft files
- renders additional original lyric drafts
- scores each draft for theme coverage, structure, hook behavior, arc support, language, and safety
- writes a markdown report plus a machine-readable manifest
