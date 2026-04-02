# Track Dossiers

This layer borrows the shape of a manual deep-analysis sheet and applies it to the corpus as structured data.

It is meant to be higher-value than:

- raw lyric text
- flat normalized documents
- shallow tag-only intent cards

## What A Dossier Stores

- track identity
- high-level song intent
- contrast device
- dramatic arc
- section-by-section function
- arrangement intent per section
- distilled SUNO conditioning
- explicit metadata gaps that still need manual enrichment

## Intended Flow

```text
raw -> normalized -> curated -> intent cards -> track dossiers -> training / prompting
```

## Why This Matters

The goal is to stop storing songs as "lyrics plus a few tags".

Instead, each record should answer:

- what is this song trying to do
- how does each section support that goal
- what contrast makes the song memorable
- what should a style prompt preserve
- what is still missing and needs manual work

## Run It

```powershell
python scripts/pipeline/build_track_dossiers.py `
  --artist-id ado `
  --project-root .
```

## Outputs

- `datasets/dossiers/<artist_id>/track_dossiers.jsonl`
- `datasets/dossiers/<artist_id>/track_dossier_manifest.json`
- `reports/dossiers/<artist_id>_track_dossier_report.md`
