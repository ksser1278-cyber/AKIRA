# Dataset Stage 4 Quarantine

Moved on `2026-04-03`.

## Purpose

Reduce `scripts/dataset` to the current rebuild-era compatibility shims only.

## Retained Active Files

- `bootstrap_training_rights_map.py`
- `build_training_datasets.py`
- `export_supervised_training_samples.py`

## Quarantined Files

- `build_all_datasets.py`
- `build_antigravity_corpus.py`
- `build_artist_training_package.py`
- `build_corpus.py`
- `build_dataset.py`
- `build_goldset_review_bundle.py`
- `build_preference_bundle.py`
- `build_songwriter_v2_bestof.py`
- `export_songwriter_v2_requests.py`
- `import_songwriter_v2_predictions.py`

## Rationale

These scripts belong to older corpus/export flows and are not part of the reduced rebuild execution surface.

They were moved, not deleted.
