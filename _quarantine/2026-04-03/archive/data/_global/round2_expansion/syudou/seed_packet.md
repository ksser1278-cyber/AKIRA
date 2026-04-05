# Round2 Seed Packet: syudou

## Purpose
This packet is for the remaining round2 candidate-only tracks that still need draft seeds before scaffold generation.

## Required Output

- Submit draft seed JSON only, not full conditioning JSON.
- Keep `track_id`, `likely_mode`, and candidate direction intact.
- Target file: `expansion_round2_draft_seeds.json`-compatible per-track payloads.

## Candidate-Only Queue

- `syudou_call_boy` / priority `high` / likely `direct_emotional_pop` / secondary `ironic_meta`
  why: Raw, alcoholic desperation.
- `syudou_bakushou` / priority `high` / likely `ironic_meta` / secondary `dark_cute_breakdown`
  why: Manic laughter as a hook device.
- `syudou_cute_na_kanojo` / priority `medium` / likely `dark_cute_breakdown` / secondary `ironic_meta`
  why: Sarcastic toxic romance.
- `syudou_gamble` / priority `medium` / likely `direct_emotional_pop` / secondary `ironic_meta`
  why: High stakes dramatic anthem.

## Draft Seed Fields

- artist_id
- track_id
- title
- likely_mode
- title_pattern
- hook_behavior
- section_flow_guess
- imagery_classes
- emotional_arc
- leakage_watchouts
- prompt_seed_terms
- grounding_status

## Incoming Directory

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\round2_expansion\syudou\seed_incoming`

## Notes

- Prefer high-priority candidates first.
- Do not output full conditioning in this step.
- This step exists only to unlock scaffold generation for the remaining round2 queue.
