# Lyric Curation

`lyrics/raw` is not a training dataset.

It is only a transport layer for scraped text files.

## Why Raw Is Weak

- file names are source IDs, not canonical track ids
- structure is not reliable enough for direct learning
- source overlap and duplicates are possible
- some titles are noisy or mixed with tie-in text
- raw files do not say whether a track is good enough for downstream use

## Intended Flow

```text
raw -> normalized -> curated -> training candidates
```

The curation step is where we decide whether a normalized lyric document is:

- `ready`
- `needs_review`
- `reject`

## Current Signals

The curator checks:

- title text quality
- lyric text quality
- section count and line count
- how many sections are still unlabeled
- whether missing labels can be recovered from inferred song form
- duplicate-title candidates

## Run It

```powershell
python scripts/pipeline/curate_lyrics_corpus.py `
  --artist-id ado `
  --project-root .
```

## Outputs

- `datasets/curated/<artist_id>/curated_tracks.jsonl`
- `datasets/curated/<artist_id>/curation_manifest.json`
- `reports/quality/<artist_id>_curation_report.md`

## Practical Meaning

After this step, the project should stop treating `raw/` as if it were training material.
Only curated records should be considered for downstream dataset shaping.
