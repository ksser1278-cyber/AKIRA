# Generation Safety Invalid Brief: neru

- invalid tracks `1`
- incoming dir `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\generation_safety_invalid\neru\incoming`

## Priority

- `neru_tokyo_teddy_bear` / blockers `missing_provenance, partial_grounding, renderer_policy_block`

## Required Output

- merge-friendly JSON only
- keep `track_id` unchanged
- restore provenance with trusted lyric and metadata sources
- replace compact grounding with section-complete lyric grounding
- leave `ready_for_prompting` false unless provenance and grounding are restored
