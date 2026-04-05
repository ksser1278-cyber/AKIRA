# Phase 1 Core Cleanup Handoff

- scope: `16` records across `6` artists
- objective: clear `partial_grounding` and `surface_noise_risk` so merged records can be re-evaluated toward `planner_safe`

## Package Use

For each artist package under this directory:
- read `packet.md` for track-by-track blocker detail
- read `brief.md` for workflow rules
- use `source_records/` as the bundled record reference
- write patch outputs into `incoming/`
- do not submit mojibake, unreadable text, replacement characters, or broken byte sequences
- do not replace placeholders with generic English summaries or meta commentary
- do not replace placeholders with inferred paraphrases; edited `sections` and `hook_lines` must use clean grounded Japanese text copied or tightly aligned from bundled `source_records/`
- do not submit English cleanup commentary in `source_provenance.notes`, `song_intent.emotional_thesis`, or `lyric_ground_truth.copyright_handling_note`
- before submission, verify zero replacement characters, zero mojibake, zero scaffold phrases, and zero English/meta commentary anywhere in edited fields
- if a track cannot be grounded into clean UTF-8 text aligned to the bundled source record, leave it unsubmitted

## Target Artists

- `iyowa`
- `kairiki_bear`
- `kanaria`
- `maretu`
- `neru`
- `syudou`

## Required Patch Scope

Patch only the fields needed to remove scaffold grounding and surface-noise issues.

Typical fields:
- `lyric_ground_truth.sections`
- `lyric_ground_truth.hook_lines`
- `source_provenance.notes`
- `song_intent.emotional_thesis`
- `lyric_ground_truth.copyright_handling_note`

## Submission Rules

- one merge-friendly JSON patch per track
- filename must be `<track_id>.json`
- keep `track_identity.track_id` stable
- keep the song meaning aligned to the bundled source record
- do not modify engine code
- do not rewrite unrelated fields
- do not change `song_intent.narrative_role` in this phase unless the bundled source record itself shows a clear local contradiction
- do not add provenance unless an explicit bundled blocker requires it
- do not submit mojibake, broken encoding, replacement characters, or malformed UTF-8 text
- do not submit English summary lines in `sections` or `hook_lines`
- do not submit inferred paraphrases in `sections` or `hook_lines`
- do not submit English cleanup commentary in notes, thesis, or copyright fields
- if exact grounded Japanese lines cannot be supplied safely, leave the field unchanged and flag the record instead
- do not submit generic English rewrite lines in `sections` or `hook_lines`

## Success Gate

Each merged record should:
- no longer trigger `partial_grounding`
- no longer trigger `surface_noise_risk`
- remain valid after merge-time recomputation
- be eligible for `planner_safe` review

## Delivery Paths

- `iyowa\\incoming`
- `kairiki_bear\\incoming`
- `kanaria\\incoming`
- `maretu\\incoming`
- `neru\\incoming`
- `syudou\\incoming`
