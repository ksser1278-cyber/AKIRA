# Phase 1 Core Cleanup Retry Handoff

- previous batch status: `16 invalid / 16 rejected`
- rejected patch archive: `..\phase1_rejected_20260328`
- objective: resubmit only clean UTF-8 grounded patches that can clear `partial_grounding` and `surface_noise_risk`

## What Failed In The Rejected Batch

The rejected batch failed for the same reason across all target artists:
- merged verdict remained `audit_only`
- blocker `partial_grounding` remained
- blocker `surface_noise_risk` remained

Observed bad patterns in rejected JSON:
- mojibake or unreadable text in `lyric_ground_truth.sections`
- broken characters in `hook_lines`
- generic English rewrite lines instead of grounded source-aligned text
- high-level paraphrase in `song_intent.emotional_thesis` without actually fixing grounded sections

## Hard Rules For Retry

- submit only valid UTF-8 JSON
- do not submit unreadable characters, replacement characters, or broken byte sequences
- do not submit English summary lines in `sections` or `hook_lines`
- do not replace placeholders with inferred paraphrases; edited `sections` and `hook_lines` must use clean grounded Japanese text copied or tightly aligned from bundled `source_records/`
- do not submit English cleanup commentary in `source_provenance.notes`, `song_intent.emotional_thesis`, or `lyric_ground_truth.copyright_handling_note`
- before submission, verify zero replacement characters, zero mojibake, zero scaffold phrases, and zero English/meta commentary anywhere in edited fields
- if clean grounded text cannot be supplied safely, do not submit that track

## Required Input Source

For each artist package:
- use `source_records/` as the only bundled input reference
- use `packet.md` to see placeholder fields and blockers
- write accepted retry patches into that artist's `incoming/`

## Submission Scope

Allowed fields:
- `lyric_ground_truth.sections`
- `lyric_ground_truth.hook_lines`
- `source_provenance.notes`
- `song_intent.emotional_thesis`
- `lyric_ground_truth.copyright_handling_note`

Do not change in this retry:
- `track_identity.track_id`
- `song_intent.narrative_role`
- provenance fields
- unrelated prompt-conditioning or analysis fields

## Pass Condition

A retry patch is acceptable only if the merged record:
- no longer triggers `partial_grounding`
- no longer triggers `surface_noise_risk`
- is eligible for `planner_safe` review after recomputation

## Example Rejected Sources

- `..\phase1_rejected_20260328\iyowa\iyowa_1000_nen_ikiteiru.json`
- `..\phase1_rejected_20260328\kanaria\kanaria_eye.json`

Read them only as negative examples. Do not reuse their section text.
