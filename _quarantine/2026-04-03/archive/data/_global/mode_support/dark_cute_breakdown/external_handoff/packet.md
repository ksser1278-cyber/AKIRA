# Mode Support Packet: dark_cute_breakdown

## Purpose
This packet is the single handoff unit for cross-producer mode support curation.

## Delivery Prompt

```text
This is a mode support curation task for `dark_cute_breakdown`.

Goal:
- Curate support tracks for each listed artist that match this mode.
- Do not create conditioning JSON yet.
- Return only candidate track ids, titles, and short justification atoms.

Rules:
- Avoid duplicating current gold anchors and active producer expansion tracks.
- Prefer tracks that diversify hook shape, section behavior, and lyrical framing.
- Keep the output structured and mode-focused.

Per-artist targets:
- `deco27` / target `5`
- `pinocchiop` / target `5`
- `kairiki_bear` / target `5`
- `maretu` / target `5`

Required output format:
- One JSON file per mode
- Include `mode_id` and an `artist_candidates` array
- Each artist entry should include `artist_id`, `candidate_track_ids`, `candidate_titles`, and `notes`
```

## Working Notes

# Mode Support Brief: dark_cute_breakdown

## Objective
Curate cross-producer support tracks that strengthen this mode without duplicating anchor or producer-expansion coverage.

## Mode Constraints
- Mode id: `dark_cute_breakdown`
- Target total count: `20`
- Support artists: `deco27, pinocchiop, kairiki_bear, maretu`

## Curation Rules
- Prefer tracks that diversify hook shape, section geometry, and phrase energy.
- Avoid near-duplicates of current gold anchors.
- Avoid active producer-expansion tracks already queued for grounding.
- Return only support candidates, not conditioning JSON.

## Excluded Track IDs

- `pinocchiop_kamippoi_na`
- `pinocchiop_tensei_ringo`
- `pinocchiop_tokumei_m`
- `pinocchiop_mahou_shoujo_to_chocolate`
- `pinocchiop_non_breath_oblige`
- `deco27_ghost_rule`
- `deco27_love_doll`
- `deco27_ai_kotoba`
- `deco27_tsumi_to_batsu`
- `deco27_yumeyume`
- `pinocchiop_aisarenakutemo_kimi_ga_iru`
- `pinocchiop_loveit`
- `pinocchiop_ultimate_senpai`
- `pinocchiop_boku_nanka_inakutemo`
- `pinocchiop_kusare_gedou_to_chocolate`
- `deco27_monitoring`
- `deco27_rabbit_hole`
- `deco27_vampire`
- `deco27_cinderella`

## Artist Targets

- `deco27` / target `5` / status `artist_curation_pending`
- `pinocchiop` / target `5` / status `artist_curation_pending`
- `kairiki_bear` / target `5` / status `artist_curation_pending`
- `maretu` / target `5` / status `artist_curation_pending`

## Current Queue

- Target count: `20`
- Support artists: `deco27, pinocchiop, kairiki_bear, maretu`

- `deco27` / status `artist_curation_pending` / target `5`
- `pinocchiop` / status `artist_curation_pending` / target `5`
- `kairiki_bear` / status `artist_curation_pending` / target `5`
- `maretu` / status `artist_curation_pending` / target `5`

## Incoming Directory

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\mode_support\dark_cute_breakdown\external_handoff\incoming`
