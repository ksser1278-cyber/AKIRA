# Round2 Seed Packet: kanaria

## Purpose
This packet is for the remaining round2 candidate-only tracks that still need draft seeds before scaffold generation.

## Required Output

- Submit draft seed JSON only, not full conditioning JSON.
- Keep `track_id`, `likely_mode`, and candidate direction intact.
- Target file: `expansion_round2_draft_seeds.json`-compatible per-track payloads.

## Candidate-Only Queue

- `kanaria_mira` / priority `medium` / likely `direct_emotional_pop` / secondary `ironic_meta`
  why: Early Kanaria track establishing baseline emotional tones.
- `kanaria_yoidore_shirazu` / priority `high` / likely `dark_cute_breakdown` / secondary `ironic_meta`
  why: Broadens Kanaria beyond loud shouts into sliding intoxication.
- `kanaria_requiem` / priority `medium` / likely `direct_emotional_pop` / secondary `dark_cute_breakdown`
  why: Hyper-energetic VTuber collaboration style.
- `kanaria_daino_tekina_rendezvous` / priority `high` / likely `ironic_meta` / secondary `direct_emotional_pop`
  why: Shows adaptation to external narrative.

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

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\round2_expansion\kanaria\seed_incoming`

## Notes

- Prefer high-priority candidates first.
- Do not output full conditioning in this step.
- This step exists only to unlock scaffold generation for the remaining round2 queue.
