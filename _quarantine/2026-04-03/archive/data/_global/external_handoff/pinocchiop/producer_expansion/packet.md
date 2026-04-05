# Producer Expansion Packet: pinocchiop

## Purpose
This packet is the single handoff unit for external producer expansion conditioning work.

## Delivery Prompt

```text
This is a producer expansion conditioning promotion task for `pinocchiop`.

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
- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\pinocchiop\producer_expansion\incoming`

Target tracks:
- `pinocchiop_aisarenakutemo_kimi_ga_iru`
  current score: `0`
  current full_text_status: `partial`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\aisarenakutemo_kimi_ga_iru.conditioning.json`
  priority: `high`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
  blockers: hook_lines missing; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
  warnings: lyric text is only partial; prompt_conditioning is sparse; audio proxy evidence_basis missing; quality_control.missing_fields has 7 entries; manual review required for 3 fields; question_lines missing

- `pinocchiop_boku_nanka_inakutemo`
  current score: `0`
  current full_text_status: `partial`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\boku_nanka_inakutemo.conditioning.json`
  priority: `high`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
  blockers: hook_lines missing; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
  warnings: lyric text is only partial; prompt_conditioning is sparse; audio proxy evidence_basis missing; quality_control.missing_fields has 7 entries; manual review required for 3 fields; question_lines missing

- `pinocchiop_kusare_gedou_to_chocolate`
  current score: `0`
  current full_text_status: `partial`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\kusare_gedou_to_chocolate.conditioning.json`
  priority: `high`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
  blockers: hook_lines missing; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
  warnings: lyric text is only partial; prompt_conditioning is sparse; audio proxy evidence_basis missing; quality_control.missing_fields has 7 entries; manual review required for 3 fields; question_lines missing

- `pinocchiop_loveit`
  current score: `0`
  current full_text_status: `partial`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\loveit.conditioning.json`
  priority: `high`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
  blockers: hook_lines missing; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
  warnings: lyric text is only partial; prompt_conditioning is sparse; audio proxy evidence_basis missing; quality_control.missing_fields has 7 entries; manual review required for 3 fields; question_lines missing

- `pinocchiop_ultimate_senpai`
  current score: `0`
  current full_text_status: `partial`
  target file: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\ultimate_senpai.conditioning.json`
  priority: `high`
  required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
  blockers: hook_lines missing; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
  warnings: lyric text is only partial; prompt_conditioning is sparse; audio proxy evidence_basis missing; quality_control.missing_fields has 7 entries; manual review required for 3 fields; question_lines missing

Required output format:
- One JSON file per track
- Include `track_identity.track_id`
- Return either a complete replacement JSON or a merge-friendly JSON payload

Success condition:
- Reduce weak records in producer expansion audit and move them toward usable or better
```

## Current Audit Summary

- Records: `5`
- Gold: `0`
- Usable: `0`
- Weak: `5`
- Average score: `0.0`

## Working Notes

# Producer Expansion Delegation Brief: pinocchiop

## Scope
- Task type: conditioning promotion from scaffolded/weak to usable or gold candidate
- Required work: full lyric grounding, provenance, hook extraction, section analysis, prompt conditioning completion, optional audio enrichment

## Track Priority

### pinocchiop_aisarenakutemo_kimi_ga_iru
- Priority: `high`
- Current score: `0`
- Current full_text_status: `partial`
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\aisarenakutemo_kimi_ga_iru.conditioning.json`
- Required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
- Blockers: hook_lines missing; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
- Warnings: lyric text is only partial; prompt_conditioning is sparse; audio proxy evidence_basis missing; quality_control.missing_fields has 7 entries; manual review required for 3 fields; question_lines missing

### pinocchiop_boku_nanka_inakutemo
- Priority: `high`
- Current score: `0`
- Current full_text_status: `partial`
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\boku_nanka_inakutemo.conditioning.json`
- Required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
- Blockers: hook_lines missing; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
- Warnings: lyric text is only partial; prompt_conditioning is sparse; audio proxy evidence_basis missing; quality_control.missing_fields has 7 entries; manual review required for 3 fields; question_lines missing

### pinocchiop_kusare_gedou_to_chocolate
- Priority: `high`
- Current score: `0`
- Current full_text_status: `partial`
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\kusare_gedou_to_chocolate.conditioning.json`
- Required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
- Blockers: hook_lines missing; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
- Warnings: lyric text is only partial; prompt_conditioning is sparse; audio proxy evidence_basis missing; quality_control.missing_fields has 7 entries; manual review required for 3 fields; question_lines missing

### pinocchiop_loveit
- Priority: `high`
- Current score: `0`
- Current full_text_status: `partial`
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\loveit.conditioning.json`
- Required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
- Blockers: hook_lines missing; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
- Warnings: lyric text is only partial; prompt_conditioning is sparse; audio proxy evidence_basis missing; quality_control.missing_fields has 7 entries; manual review required for 3 fields; question_lines missing

### pinocchiop_ultimate_senpai
- Priority: `high`
- Current score: `0`
- Current full_text_status: `partial`
- Target: `C:\JPop_Songwriter\AKIRA ENGINE\data\pinocchiop\reference_tracks\ultimate_senpai.conditioning.json`
- Required work: full_lyric_grounding, section_analysis_expansion, source_provenance_strengthening, prompt_conditioning_completion, audio_enrichment_if_available
- Blockers: hook_lines missing; ready_for_prompting is false; high-trust evidence ratio is too low; lyric_sources missing; metadata_sources missing
- Warnings: lyric text is only partial; prompt_conditioning is sparse; audio proxy evidence_basis missing; quality_control.missing_fields has 7 entries; manual review required for 3 fields; question_lines missing

## Incoming Directory

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\pinocchiop\producer_expansion\incoming`

## After Return

```powershell
python C:\JPop_Songwriter\AKIRA ENGINE\scripts\pipeline\run_producer_expansion_roundtrip.py --artist-id pinocchiop --input-dir "C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\pinocchiop\producer_expansion\incoming" --project-root "C:\JPop_Songwriter\AKIRA ENGINE" --backup
```
