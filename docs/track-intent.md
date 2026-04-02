# Track Intent

Lyrics alone are not enough.

For SUNO-facing generation, the system also needs to know what job a song is doing.

Examples:

- opening or theme-song anchor
- insert-song emotional peak
- brand or commercial hook
- collaboration spotlight
- inward confession
- night-drive momentum

## Intent Flow

```text
raw -> normalized -> curated -> track intent cards -> training / prompting
```

The intent layer combines:

- title annotations and tie-in metadata
- Spotify release context
- inferred song form
- imagery / emotion / hook signals from lyric analysis

## Outputs

- `datasets/intent/<artist_id>/track_intent_cards.jsonl`
- `datasets/intent/<artist_id>/intent_manifest.json`
- `reports/intent/<artist_id>_track_intent_report.md`

## Run It

```powershell
python scripts/pipeline/build_track_intent_cards.py `
  --artist-id ado `
  --project-root .
```

## Why It Matters

This layer helps the project stop treating every song as the same kind of training sample.

Instead of only learning:

- imagery
- structure
- hook density

the system can also condition on:

- what the song is for
- how visible or event-like it should feel
- whether it should behave like a tie-in anthem, a scene intensifier, or a private confession
