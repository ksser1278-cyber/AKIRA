# Scripts Stage 6 Quarantine

Moved on `2026-04-03`.

## Purpose

Remove top-level ad-hoc script files from the active rebuild surface.

## Quarantined Files

- `audio_scraper.py`
- `audit_factory.py`
- `audit_synthesizer.py`
- `compare_pivots.py`
- `curate_mastery_bundle.py`
- `evolve_mastery.py`
- `generate_current_masterpiece.py`
- `package_suno_manifest.py`
- `phonetic_demo_hyper.py`
- `run_mastery_batch.py`
- `_hook_research.py`
- `_motif_research.py`

## Rationale

These files were not part of the current `akira.py` surface and made the root of `scripts/` look busier than the actual active rebuild workflow.

They were moved, not deleted.
