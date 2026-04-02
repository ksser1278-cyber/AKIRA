# Audio Analysis

## Purpose

Audio analysis should begin with measurable file facts before any higher-level sound interpretation.

The first implemented layer is intentionally narrow:

- file existence
- container / codec
- sample rate
- channels
- duration
- bitrate
- file size

This is the minimum trustable audio layer because it comes from `ffprobe`, not inference.

## Inputs

- `data/audio_manifest.json`

## Script

```powershell
python scripts/pipeline/analyze_audio_manifest.py `
  --project-root .
```

## Outputs

- `reports/audio/audio_analysis_summary.json`
- `reports/audio/audio_analysis_summary.md`

## Why This Matters

Before this layer, the project had almost no trustworthy audio facts.

That made `audio_fact_layer` weak because most sound claims were still proxy inference.

This layer does not solve stylistic sound understanding yet, but it does establish:

- file-to-track provenance
- measurable duration
- measurable codec/sample-rate/channel facts
- a stable base for later loudness, tempo, and spectral analysis

## Next Expansion

After file-fact analysis is stable, the next steps are:

1. tempo estimation
2. loudness / dynamics summary
3. onset density / section energy curve
4. later, controlled enrichment of `audio_fact_layer`
