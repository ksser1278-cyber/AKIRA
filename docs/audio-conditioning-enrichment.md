# Audio Conditioning Enrichment

## Purpose

Once owned audio files are mapped and measured, the project can promote a subset of audio claims from proxy inference into measured facts.

This enrichment step writes measured audio metadata back into each `track_conditioning_record`.

## Script

```powershell
python scripts/pipeline/enrich_conditioning_with_audio.py `
  --artist-id pinocchiop `
  --project-root .
```

## Inputs

- `data/audio_manifest.json`
- `reports/audio/audio_analysis_summary.json`
- `data/<artist_id>/reference_tracks/*.conditioning.json`

## What Gets Enriched

- `track_identity.release.runtime`
- `audio_fact_layer.reported_facts.audio_file_probe`
- `audio_fact_layer.reported_facts.measured_audio_profile`
- proxy notes in `audio_fact_layer.proxy_inference`
- `quality_control.warnings`

## Important Boundary

This step does **not** claim:

- exact BPM
- exact key
- exact instrumentation
- section-level arrangement truth

It only upgrades claims that are directly measurable from the owned file or safely derived from those measurements.
