# Generation Safety Invalid Brief: kanaria

- invalid tracks `2`
- incoming dir `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\generation_safety_invalid\kanaria\incoming`

## Priority

- `kanaria_king` / blockers `missing_provenance, partial_grounding, renderer_policy_block`
- `kanaria_queen` / blockers `missing_provenance, partial_grounding, renderer_policy_block`

## Required Output

- merge-friendly JSON only
- keep `track_id` unchanged
- restore provenance with trusted lyric and metadata sources
- replace compact grounding with section-complete lyric grounding
- leave `ready_for_prompting` false unless provenance and grounding are restored
