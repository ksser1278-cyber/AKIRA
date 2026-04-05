# Anchor Handoff Packet: deco27

## Purpose
This packet is the single handoff unit for active anchor conditioning maintenance.

## Delivery Prompt

```text
This is an anchor conditioning maintenance task for `deco27`.

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
- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\deco27\incoming`

Target tracks:
- `deco27_ghost_rule`
  current score: `98`
  current full_text_status: `full`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\ghost_rule.conditioning.json`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available
  warnings: manual review required for 1 fields

- `deco27_love_doll`
  current score: `98`
  current full_text_status: `full`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\love_doll.conditioning.json`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available
  warnings: manual review required for 1 fields

- `deco27_ai_kotoba`
  current score: `98`
  current full_text_status: `full`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\ai_kotoba.conditioning.json`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available
  warnings: manual review required for 1 fields

- `deco27_tsumi_to_batsu`
  current score: `98`
  current full_text_status: `full`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\tsumi_to_batsu.conditioning.json`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available
  warnings: manual review required for 1 fields

- `deco27_yumeyume`
  current score: `98`
  current full_text_status: `full`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\yumeyume.conditioning.json`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available
  warnings: manual review required for 1 fields

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
- Average score: `98.0`

## Handoff Manifest

# External Handoff: deco27

- Target dir: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks`
- Track count: `5`

## Tracks

### deco27_ghost_rule
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\ghost_rule.conditioning.json`
- Current full_text_status: `full`
- ready_for_prompting: `True`
- External work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available

### deco27_love_doll
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\love_doll.conditioning.json`
- Current full_text_status: `full`
- ready_for_prompting: `True`
- External work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available

### deco27_ai_kotoba
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\ai_kotoba.conditioning.json`
- Current full_text_status: `full`
- ready_for_prompting: `True`
- External work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available

### deco27_tsumi_to_batsu
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\tsumi_to_batsu.conditioning.json`
- Current full_text_status: `full`
- ready_for_prompting: `True`
- External work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available

### deco27_yumeyume
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\yumeyume.conditioning.json`
- Current full_text_status: `full`
- ready_for_prompting: `True`
- External work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, audio_enrichment_if_available

## Incoming Directory

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\deco27\incoming`

## After Return

```powershell
python C:\JPop_Songwriter\AKIRA ENGINE\scripts\pipeline\run_anchor_external_roundtrip.py --artist-id deco27 --input-dir "C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\deco27\incoming" --project-root "C:\JPop_Songwriter\AKIRA ENGINE" --backup
```
