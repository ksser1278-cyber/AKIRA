# Round2 Seed Packet: pinocchiop

## Purpose
This packet is for the remaining round2 candidate-only tracks that still need draft seeds before scaffold generation.

## Required Output

- Submit draft seed JSON only, not full conditioning JSON.
- Keep `track_id`, `likely_mode`, and candidate direction intact.
- Target file: `expansion_round2_draft_seeds.json`-compatible per-track payloads.

## Candidate-Only Queue

- `pinocchiop_apple_dot_com` / priority `high` / likely `ironic_meta` / secondary `dark_cute_breakdown`
  why: High conceptual irony using digital branding.
- `pinocchiop_motivation_is_dead` / priority `medium` / likely `ironic_meta` / secondary `direct_emotional_pop`
  why: Ultimate apathy anthem.
- `pinocchiop_nee_nee_nee` / priority `high` / likely `dark_cute_breakdown` / secondary `ironic_meta`
  why: Dialog-driven toxic cuteness.
- `pinocchiop_suki_na_koto_dake_de_ii_desu` / priority `high` / likely `ironic_meta` / secondary `direct_emotional_pop`
  why: Sarcastic take on modern leisure.

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

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\round2_expansion\pinocchiop\seed_incoming`

## Notes

- Prefer high-priority candidates first.
- Do not output full conditioning in this step.
- This step exists only to unlock scaffold generation for the remaining round2 queue.
