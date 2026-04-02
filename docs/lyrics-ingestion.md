# Lyrics Ingestion

## Why This Is Step 1

If the project eventually learns from lyrics, the first reliable step is not prompt generation. It is collecting lyric source files in a consistent format.

This repository now starts the pipeline in this order:

1. collect lyric files locally
2. normalize them into machine-readable JSON
3. analyze those normalized documents
4. derive artist profiles and dataset records
5. generate blueprints and prompt packages

## What This Step Does

The ingestion pipeline converts local lyric files into structured documents with:

- track metadata
- normalized text
- detected sections
- per-track statistics

This is safer and more controllable than jumping straight to scraping or generation.

## Command

```powershell
python normalize_lyrics.py `
  --manifest lyrics/manifests/demo_manifest.json
```

## Expected Output

The command writes normalized JSON files to:

- `lyrics/normalized/<artist_id>/<track_id>.json`

## Important Boundary

This step is designed for lyric files you already have permission to use or that you provide manually.

It does not yet scrape lyric sites directly.
