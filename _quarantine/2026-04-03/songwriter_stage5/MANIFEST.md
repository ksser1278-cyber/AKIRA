# Songwriter Stage 5 Quarantine

Moved on `2026-04-03`.

## Purpose

Reduce `scripts/songwriter` to the single rebuild-era compatibility shim only.

## Retained Active File

- `run_demo_songwriter.py`

## Quarantined Files

- `batch_smoke_tests.py`
- `generate_anchor_batches.py`
- `generate_lyrics_batch.py`
- `generate_lyric_draft.py`
- `generate_prompt_package.py`
- `run_anchor_track_matrix.py`
- `run_demo_planner.py`
- `run_freestyle.py`
- `run_gemini_songwriter_requests.py`
- `run_gemini_songwriter_revision_roundtrip.py`
- `run_gemini_songwriter_roundtrip.py`
- `run_gemini_songwriter_section_rewrite_roundtrip.py`
- `run_lyric_draft_batch_test.py`
- `run_maretu_freestyle.py`
- `run_maretu_somatic_freestyle.py`
- `run_pure_visual.py`
- `run_representative_demo_set.py`
- `run_songwriter_v2.py`
- `run_songwriter_v2_batch.py`
- `run_song_package_pipeline.py`

## Rationale

These scripts represent older manual demo, batch, freestyle, and roundtrip flows that are outside the reduced rebuild entry surface.

They were moved, not deleted.
