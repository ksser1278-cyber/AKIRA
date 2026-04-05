# Scripts Surface

`akira.py` is the primary entrypoint.

`scripts/` remains only for:

- compatibility shims
- batch utilities not yet internalized
- research and ingest tooling that still needs triage

The top-level `scripts/` root no longer contains active executable `.py` files.
Only subdirectories plus this README remain.

## Current Active Buckets

- `dataset/`
  - dataset derivation, rights bootstrap, supervised export
- `songwriter/`
  - songwriter-oriented wrappers and batch helpers
- `pipeline/`
  - report and legacy pipeline operations pending consolidation
- `ingest/`
  - corpus and metadata acquisition tools pending consolidation
- `eval/`
  - evaluation set and benchmark tooling pending consolidation
- `analysis/`, `ops/`, `production/`, `research/`, `suno/`
  - retained for later triage

## Already Internalized Behind `akira.py`

- songwriter demo
- dataset build-derived
- dataset bootstrap-rights
- dataset export-supervised
- report engine-health
- report baseline

## Quarantined Stage 2

The following were moved out of the active `scripts/` surface:

- `oneoff/`
- ad-hoc smoke scripts
- ad-hoc weekly test scripts
- `verify_phase_5.py`
- `autonomous_cycle_demo.py`
- `mastery_demo_run.py`

Location:

- `C:\JPop_Songwriter\AKIRA ENGINE\_quarantine\2026-04-03\scripts_stage2`

## Next Reduction Target

The next safe reduction is:

1. replace selected `pipeline/` scripts with `src/akira_engine/cli/` commands
2. reduce `pipeline/` to conditioning/corpus helpers only
3. triage `ingest/`, `eval/`, `analysis/`, `ops/`, `production/`, `research/`, and `suno/`
