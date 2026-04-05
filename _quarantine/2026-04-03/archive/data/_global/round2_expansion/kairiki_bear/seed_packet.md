# Round2 Seed Packet: kairiki_bear

## Purpose
This packet is for the remaining round2 candidate-only tracks that still need draft seeds before scaffold generation.

## Required Output

- Submit draft seed JSON only, not full conditioning JSON.
- Keep `track_id`, `likely_mode`, and candidate direction intact.
- Target file: `expansion_round2_draft_seeds.json`-compatible per-track payloads.

## Candidate-Only Queue

- `kairiki_bear_angel` / priority `high` / likely `dark_cute_breakdown` / secondary `direct_emotional_pop`
  why: Adds heavy angelic/demonic binary theme.
- `kairiki_bear_alkali_rettoushou` / priority `medium` / likely `ironic_meta` / secondary `dark_cute_breakdown`
  why: Establishes inferiority complex themes clearly.
- `kairiki_bear_lemmingming` / priority `medium` / likely `dark_cute_breakdown` / secondary `ironic_meta`
  why: Explores mass psychology and suicidal ideation metaphors.
- `kairiki_bear_shippaisaku_shoujo` / priority `high` / likely `direct_emotional_pop` / secondary `dark_cute_breakdown`
  why: Deeply emotional, less glitchy, more desperate.

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

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\round2_expansion\kairiki_bear\seed_incoming`

## Notes

- Prefer high-priority candidates first.
- Do not output full conditioning in this step.
- This step exists only to unlock scaffold generation for the remaining round2 queue.
