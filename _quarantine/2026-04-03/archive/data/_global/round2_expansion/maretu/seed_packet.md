# Round2 Seed Packet: maretu

## Purpose
This packet is for the remaining round2 candidate-only tracks that still need draft seeds before scaffold generation.

## Required Output

- Submit draft seed JSON only, not full conditioning JSON.
- Keep `track_id`, `likely_mode`, and candidate direction intact.
- Target file: `expansion_round2_draft_seeds.json`-compatible per-track payloads.

## Candidate-Only Queue

- `maretu_umitagari` / priority `medium` / likely `dark_cute_breakdown` / secondary `direct_emotional_pop`
  why: Addresses toxic obsessive love in a different meter.
- `maretu_white_happy` / priority `high` / likely `ironic_meta` / secondary `dark_cute_breakdown`
  why: Sarcastic faux-happiness.
- `maretu_koukatsu` / priority `medium` / likely `ironic_meta` / secondary `direct_emotional_pop`
  why: Sharp, biting social critique.
- `maretu_darling` / priority `high` / likely `direct_emotional_pop` / secondary `dark_cute_breakdown`
  why: Highly requested for intense emotional anchors.

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

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\round2_expansion\maretu\seed_incoming`

## Notes

- Prefer high-priority candidates first.
- Do not output full conditioning in this step.
- This step exists only to unlock scaffold generation for the remaining round2 queue.
