# Mode Support Packet: ironic_meta

## Purpose
This packet is the single handoff unit for cross-producer mode support curation.

## Delivery Prompt

```text
This is a mode support curation task for `ironic_meta`.

Goal:
- Curate support tracks for each listed artist that match this mode.
- Do not create conditioning JSON yet.
- Return only candidate track ids, titles, and short justification atoms.

Rules:
- Avoid duplicating current gold anchors and active producer expansion tracks.
- Prefer tracks that diversify hook shape, section behavior, and lyrical framing.
- Keep the output structured and mode-focused.

Per-artist targets:
- `pinocchiop` / target `6`
- `kanaria` / target `6`
- `maretu` / target `6`

Required output format:
- One JSON file per mode
- Include `mode_id` and an `artist_candidates` array
- Each artist entry should include `artist_id`, `candidate_track_ids`, `candidate_titles`, and `notes`
```

## Working Notes

# Mode Support Brief: ironic_meta

## Objective
Curate cross-producer support tracks that strengthen this mode without duplicating anchor or producer-expansion coverage.

## Mode Constraints
- Mode id: `ironic_meta`
- Target total count: `20`
- Support artists: `pinocchiop, kanaria, maretu`

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

- `pinocchiop` / target `6` / status `artist_curation_pending`
- `kanaria` / target `6` / status `artist_curation_pending`
- `maretu` / target `6` / status `artist_curation_pending`

## Current Queue

- Target count: `20`
- Support artists: `pinocchiop, kanaria, maretu`

- `pinocchiop` / status `artist_curation_pending` / target `6`
- `kanaria` / status `artist_curation_pending` / target `6`
- `maretu` / status `artist_curation_pending` / target `6`

## Incoming Directory

- `C:\JPop_Songwriter\AKIRA ENGINE\data\_global\mode_support\ironic_meta\external_handoff\incoming`
