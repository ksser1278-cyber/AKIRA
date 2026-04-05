# Generation Safety Invalid Packet: iyowa

## Purpose
Restore invalid conditioning records to at least audit-only or planner-safe status by fixing provenance and grounding gaps.

## Tracks

- `iyowa_kyukurarin` / score `0.23` / blockers `missing_provenance, partial_grounding, mode_fit_unverified` / next `add lyric_sources and metadata_sources with trusted statuses`

## Incoming Directory

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\generation_safety_invalid\iyowa\incoming`

## Required Upgrades

- add trusted `lyric_sources` and `metadata_sources`
- replace compact or chorus-only grounding with section-complete lyric grounding
- keep `ready_for_prompting` disabled until provenance and grounding are restored
- add mode alignment where `mode_fit_unverified` is present
