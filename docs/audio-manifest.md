# Audio Manifest

## Purpose

The project now treats owned audio files as an external library and maps them into the engine with a manifest.

This avoids:

- copying large audio files into the repository
- losing provenance
- ambiguous filename-to-track matching

## Canonical File

- `data/audio_manifest.json`

## Current Source Root

- `C:\Users\hangi\OneDrive\문서\멜론 보관함\받은 파일함`

## Mapping Rule

Each entry should map:

- `track_id`
- `artist_id`
- `title`
- `source_filename`
- `source_path`
- `audio_format`
- `status`
- `provenance`

## Current Owned Set

### PinocchioP

- `pinocchiop_kamippoi_na`
- `pinocchiop_tensei_ringo`
- `pinocchiop_tokumei_m`
- `pinocchiop_mahou_shoujo_to_chocolate`
- `pinocchiop_non_breath_oblige`

### DECO*27

- `deco27_ghost_rule`
- `deco27_love_doll`
- `deco27_ai_kotoba`
- `deco27_tsumi_to_batsu`
- `deco27_yumeyume`

## Operational Rule

Do not treat audio ownership as equivalent to conditioning quality.

Audio files only improve the `audio_fact_layer` if:

1. the file is mapped to a canonical `track_id`
2. the analysis path writes results back with explicit provenance
3. technical claims stay separate from lyric-grounded interpretation

## Next Step

Build an audio analysis layer that reads `data/audio_manifest.json` and emits:

- `reported_facts` updates where measurable
- `audio_required_claims` for claims that should only exist when actual audio is available
- stronger `proxy_inference` confidence boundaries
