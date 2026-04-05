# Generation Safety Invalid Brief: syudou

- invalid tracks `2`
- incoming dir `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\generation_safety_invalid\syudou\incoming`

## Priority

- `syudou_bitter_choco_decoration` / blockers `missing_provenance, partial_grounding, renderer_policy_block`
- `syudou_usseewa` / blockers `missing_provenance, partial_grounding, renderer_policy_block`

## Required Output

- merge-friendly JSON only
- keep `track_id` unchanged
- restore provenance with trusted lyric and metadata sources
- replace compact grounding with section-complete lyric grounding
- leave `ready_for_prompting` false unless provenance and grounding are restored
