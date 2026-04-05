# Anchor Handoff Packet: pinocchiop

## Purpose
This packet is the single handoff unit for active anchor conditioning maintenance.

## Delivery Prompt

```text
This is an anchor conditioning maintenance task for `pinocchiop`.

Goal:
- Keep active anchor conditioning records at gold quality.
- Strengthen provenance, section detail, and audio-linked notes without changing the existing schema.
- This is dataset maintenance, not songwriting.

Rules:
- Keep `lyric_ground_truth.full_text_status` at `full` when justified by the returned data.
- Preserve the existing track identity and track_id.
- Distinguish `confirmed`, `cross_checked`, `estimated`, and `inferred`.
- Do not weaken provenance or remove existing grounded sections.
- Return JSON only.

Output directory:
- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\pinocchiop\incoming`

Target tracks:
- `pinocchiop_kamippoi_na`
  current score: `97`
  current full_text_status: `full`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\kamippoi_na.conditioning.json`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available
  warnings: manual review required for 1 fields; question_lines missing

- `pinocchiop_tensei_ringo`
  current score: `98`
  current full_text_status: `full`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\tensei_ringo.conditioning.json`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available
  warnings: manual review required for 1 fields

- `pinocchiop_tokumei_m`
  current score: `98`
  current full_text_status: `full`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\tokumei_m.conditioning.json`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available
  warnings: manual review required for 1 fields

- `pinocchiop_mahou_shoujo_to_chocolate`
  current score: `97`
  current full_text_status: `full`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\mahou_shoujo_to_chocolate.conditioning.json`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available
  warnings: manual review required for 1 fields; question_lines missing

- `pinocchiop_non_breath_oblige`
  current score: `96`
  current full_text_status: `full`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\non_breath_oblige.conditioning.json`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available
  warnings: manual review required for 2 fields

Required output format:
- One JSON file per track
- Include `track_identity.track_id`
- Return either a complete replacement JSON or a merge-friendly JSON payload
```

## Current Audit Summary

- Records: `5`
- Gold: `5`
- Usable: `0`
- Weak: `0`
- Average score: `97.2`

## Handoff Manifest

# External Handoff: pinocchiop

- Target dir: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks`
- Track count: `5`

## Tracks

### pinocchiop_kamippoi_na
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\kamippoi_na.conditioning.json`
- Current full_text_status: `full`
- ready_for_prompting: `True`
- External work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available

### pinocchiop_tensei_ringo
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\tensei_ringo.conditioning.json`
- Current full_text_status: `full`
- ready_for_prompting: `True`
- External work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available

### pinocchiop_tokumei_m
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\tokumei_m.conditioning.json`
- Current full_text_status: `full`
- ready_for_prompting: `True`
- External work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available

### pinocchiop_mahou_shoujo_to_chocolate
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\mahou_shoujo_to_chocolate.conditioning.json`
- Current full_text_status: `full`
- ready_for_prompting: `True`
- External work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available

### pinocchiop_non_breath_oblige
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\non_breath_oblige.conditioning.json`
- Current full_text_status: `full`
- ready_for_prompting: `True`
- External work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available

## Incoming Directory

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\pinocchiop\incoming`

## After Return

```powershell
python C:\JPop_Songwriter\AKIRA ENGINE\scripts\pipeline\run_anchor_external_roundtrip.py --artist-id pinocchiop --input-dir "C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\pinocchiop\incoming" --project-root "C:\JPop_Songwriter\AKIRA ENGINE" --backup
```
