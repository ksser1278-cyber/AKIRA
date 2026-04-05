# Dataset Surface

`akira.py` is the primary entrypoint.

Active `scripts/dataset/` now exists only as a compatibility surface for three rebuild-era commands:

- `build_training_datasets.py`
- `extract_lyric_technique_records.py`
- `bootstrap_training_rights_map.py`
- `export_supervised_training_samples.py`
- `import_owned_original_hook_pilot.py`
- `build_supervised_training_pilot.py`
- `export_vertex_supervised_jsonl.py`

`build_training_datasets.py` supports a reduced-workspace fallback:

- if active lyric-analysis inputs are absent
- and archived derived JSONL exists
- the command hydrates `datasets/training/` from archive instead of rebuilding from raw analysis

Each of these delegates to internal command modules in:

- `C:\JPop_Songwriter\AKIRA ENGINE\src\akira_engine\cli`

## Internalized Coverage

- `akira.py dataset build-derived`
- `akira.py dataset extract-technique-records`
- `akira.py dataset bootstrap-rights`
- `akira.py dataset export-supervised`
- `akira.py dataset import-training-sources`
- `akira.py dataset build-training-pilot`
- `akira.py dataset export-vertex-supervised`
- `akira.py dataset seed-vocadb-metadata`

## Stage 4 Quarantine

Legacy dataset builders and exchange scripts were moved out of the active surface.

Location:

- `C:\JPop_Songwriter\AKIRA ENGINE\_quarantine\2026-04-03\dataset_stage4`

## Rule

Do not add new user-facing entrypoints here first.

Add them to `akira.py` and `src/akira_engine/cli/` first, then keep `scripts/dataset/` only if a shim is still needed.
