# Round2 Seed Packet: deco27

## Purpose
This packet is for the remaining round2 candidate-only tracks that still need draft seeds before scaffold generation.

## Required Output

- Submit draft seed JSON only, not full conditioning JSON.
- Keep `track_id`, `likely_mode`, and candidate direction intact.
- Target file: `expansion_round2_draft_seeds.json`-compatible per-track payloads.

## Candidate-Only Queue

- `deco27_mozaik_role` / priority `high` / likely `ironic_meta` / secondary `direct_emotional_pop`
  why: Classic baseline for DECO*27 rock.
- `deco27_yowamushi_montblanc` / priority `medium` / likely `direct_emotional_pop` / secondary `dark_cute_breakdown`
  why: Softer, more acoustic-driven anxiety.
- `deco27_salamander` / priority `high` / likely `ironic_meta` / secondary `direct_emotional_pop`
  why: Modern heavily-produced hip-hop/rock fusion.
- `deco27_android_girl` / priority `high` / likely `direct_emotional_pop` / secondary `none`
  why: Vocal processing as narrative device.

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

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\round2_expansion\deco27\seed_incoming`

## Notes

- Prefer high-priority candidates first.
- Do not output full conditioning in this step.
- This step exists only to unlock scaffold generation for the remaining round2 queue.
