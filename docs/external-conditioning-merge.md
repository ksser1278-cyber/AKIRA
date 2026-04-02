# External Conditioning Merge

## Purpose

Accept externally enriched conditioning JSON files, merge them into the canonical `reference_tracks` records, and then re-run audit and benchmark steps.

## Input Contract

- One JSON file per track
- File naming is flexible
- Each JSON must contain either:
  - `track_identity.track_id`, or
  - top-level `track_id`

The merge target is resolved against:

- `C:\JPop_Songwriter\AKIRA ENGINE\data\<artist_id>\reference_tracks`

## Merge Rule

- dictionaries are deep-merged
- scalar values from the external file replace existing values
- lists of objects are replaced by the incoming list
- lists of scalars are de-duplicated and unioned

This is intended for:

- provenance enrichment
- full lyric grounding
- section_analysis expansion
- audio_fact_layer enrichment
- prompt_conditioning densification

## Command

```powershell
python scripts/pipeline/merge_external_conditioning.py `
  --artist-id deco27 `
  --input-dir C:\path\to\gemini_output `
  --project-root C:\JPop_Songwriter\AKIRA ENGINE `
  --backup
```

## Expected Follow-Up

After merge:

1. re-run audit
2. re-run engine health
3. decide whether any records can move from `usable` to `gold`

Recommended commands:

```powershell
python scripts/pipeline/audit_conditioning_records.py `
  --artist-id deco27 `
  --project-root C:\JPop_Songwriter\AKIRA ENGINE `
  --active-queue-only

python scripts/pipeline/report_engine_health.py
```
