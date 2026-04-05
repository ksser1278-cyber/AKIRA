# Generation Safety Invalid Brief: kairiki_bear

- invalid tracks `4`
- incoming dir `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\generation_safety_invalid\kairiki_bear\incoming`

## Priority

- `kairiki_bear_darling_dance` / blockers `missing_provenance, partial_grounding, mode_fit_unverified, renderer_policy_block`
- `kairiki_bear_bug` / blockers `missing_provenance, partial_grounding, renderer_policy_block`
- `kairiki_bear_failure_girl` / blockers `missing_provenance, partial_grounding, renderer_policy_block`
- `kairiki_bear_ruma` / blockers `missing_provenance, partial_grounding, renderer_policy_block`

## Required Output

- merge-friendly JSON only
- keep `track_id` unchanged
- restore provenance with trusted lyric and metadata sources
- replace compact grounding with section-complete lyric grounding
- leave `ready_for_prompting` false unless provenance and grounding are restored
