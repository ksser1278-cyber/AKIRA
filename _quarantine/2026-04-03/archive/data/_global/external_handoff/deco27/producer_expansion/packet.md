# Producer Expansion Packet: deco27

## Purpose
This packet is the single handoff unit for external producer expansion conditioning work.

## Delivery Prompt

```text
This is a producer expansion conditioning promotion task for `deco27`.

Goal:
- Promote scaffolded or weak conditioning records to usable or gold-candidate quality.
- This is dataset enrichment work, not songwriting.
- Keep the existing JSON schema unchanged.

Rules:
- If full lyric grounding is possible, set `lyric_ground_truth.full_text_status` to `full`.
- If full grounding is not possible, keep it partial and state the limitation honestly.
- Distinguish `confirmed`, `cross_checked`, `estimated`, and `inferred`.
- Fill `source_provenance.lyric_sources` and `source_provenance.metadata_sources`.
- Target at least 5 `section_analysis` entries. If not possible, provide at least 3 and note the limitation.
- Do not leave `hook_lines`, `question_lines`, `prompt_conditioning`, or `quality_control` empty.
- Output JSON only. Do not return free-form commentary.

Output directory:
- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\deco27\producer_expansion\incoming`

Target tracks:
- `deco27_cinderella`
  current score: `39`
  current full_text_status: `partial`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\cinderella.conditioning.json`
  priority: `high`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
  blockers: lyric_ground_truth.sections has fewer than 3 sections; section_analysis has fewer than 3 entries; metadata_sources missing
  warnings: lyric text is only partial; only one hook line recorded; quality_control.missing_fields has 2 entries; manual review required for 2 fields

- `deco27_monitoring`
  current score: `47`
  current full_text_status: `partial`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\monitoring.conditioning.json`
  priority: `high`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
  blockers: lyric_ground_truth.sections has fewer than 3 sections; section_analysis has fewer than 3 entries
  warnings: lyric text is only partial; only one hook line recorded; quality_control.missing_fields has 2 entries; manual review required for 2 fields

- `deco27_rabbit_hole`
  current score: `49`
  current full_text_status: `partial`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\rabbit_hole.conditioning.json`
  priority: `high`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
  blockers: lyric_ground_truth.sections has fewer than 3 sections; section_analysis has fewer than 3 entries
  warnings: lyric text is only partial; only one hook line recorded; quality_control.missing_fields has 1 entries; manual review required for 2 fields

- `deco27_vampire`
  current score: `96`
  current full_text_status: `full`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\vampire.conditioning.json`
  priority: `low`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
  blockers: none
  warnings: quality_control.missing_fields has 1 entries; manual review required for 1 fields

Required output format:
- One JSON file per track
- Include `track_identity.track_id`
- Return either a complete replacement JSON or a merge-friendly JSON payload

Success condition:
- Reduce weak records in producer expansion audit and move them toward usable or better
```

## Current Audit Summary

- Records: `4`
- Gold: `1`
- Usable: `0`
- Weak: `3`
- Average score: `57.75`

## Working Notes

# Producer Expansion Delegation Brief: deco27

## Scope
- Task type: conditioning promotion from scaffolded/weak to usable or gold candidate
- Required work: full lyric grounding, provenance, hook extraction, section analysis, prompt conditioning completion, optional audio enrichment

## Track Priority

### deco27_cinderella
- Priority: `high`
- Current score: `39`
- Current full_text_status: `partial`
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\cinderella.conditioning.json`
- Required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
- Blockers: lyric_ground_truth.sections has fewer than 3 sections; section_analysis has fewer than 3 entries; metadata_sources missing
- Warnings: lyric text is only partial; only one hook line recorded; quality_control.missing_fields has 2 entries; manual review required for 2 fields

### deco27_monitoring
- Priority: `high`
- Current score: `47`
- Current full_text_status: `partial`
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\monitoring.conditioning.json`
- Required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
- Blockers: lyric_ground_truth.sections has fewer than 3 sections; section_analysis has fewer than 3 entries
- Warnings: lyric text is only partial; only one hook line recorded; quality_control.missing_fields has 2 entries; manual review required for 2 fields

### deco27_rabbit_hole
- Priority: `high`
- Current score: `49`
- Current full_text_status: `partial`
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\rabbit_hole.conditioning.json`
- Required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
- Blockers: lyric_ground_truth.sections has fewer than 3 sections; section_analysis has fewer than 3 entries
- Warnings: lyric text is only partial; only one hook line recorded; quality_control.missing_fields has 1 entries; manual review required for 2 fields

### deco27_vampire
- Priority: `low`
- Current score: `96`
- Current full_text_status: `full`
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\deco27\reference_tracks\vampire.conditioning.json`
- Required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
- Blockers: none
- Warnings: quality_control.missing_fields has 1 entries; manual review required for 1 fields

## Incoming Directory

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\deco27\producer_expansion\incoming`

## After Return

```powershell
python C:\JPop_Songwriter\AKIRA ENGINE\scripts\pipeline\run_producer_expansion_roundtrip.py --artist-id deco27 --input-dir "C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\deco27\producer_expansion\incoming" --project-root "C:\JPop_Songwriter\AKIRA ENGINE" --backup
```
