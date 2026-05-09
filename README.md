# AKIRA ENGINE

AKIRA ENGINE is a reduced rebuild workspace for a Japanese lyric-generation system.

The current goal is not to preserve every historical execution path.
The goal is to keep a small, explicit surface and rebuild upward from stable core modules.

Current scale guidance:
- build for open-ended Vocaloid corpus accumulation
- use numeric milestones only as checkpoints
- do not treat any current number as a top-level cap

## Active Workspace

Top-level active structure:

- `src/`
- `schemas/`
- `docs/`
- `tests/`
- `config/`
- `scripts/`
- `akira.py`

Historical assets, legacy outputs, and older workflow surfaces were moved to:

- `C:\JPop_Songwriter\AKIRA ENGINE\_quarantine\2026-04-03`

## Primary Entry Point

Use `akira.py` first.

```powershell
python akira.py status
python akira.py songwriter demo --artist-id maretu --mode-id dark_cute_breakdown
python akira.py dataset build-derived
python akira.py dataset bootstrap-rights
python akira.py dataset export-supervised
python akira.py dataset import-training-sources
python akira.py workflow validate
python akira.py report engine-health
python akira.py report baseline
python akira.py test
```

Detailed command notes:

- [C:\JPop_Songwriter\AKIRA ENGINE\docs\cli-skeleton.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\cli-skeleton.md)

## Current Command Coverage

Already internalized behind `akira.py` and `src/akira_engine/cli/`:

- songwriter demo
- dataset build-derived
- dataset bootstrap-rights
- dataset export-supervised
- dataset import-training-sources
- workflow validate
- report engine-health
- report baseline

Compatibility shims remain in `scripts/` only where needed.

## Scripts Policy

`scripts/` is no longer the main user-facing surface.

Current intent:

- `scripts/dataset/`: compatibility shims only
- `scripts/songwriter/`: compatibility shim only
- `scripts/pipeline/`: reduced legacy helper surface
- `scripts/ingest/`, `scripts/eval/`, `scripts/analysis/`, `scripts/ops/`, `scripts/production/`, `scripts/research/`, `scripts/suno/`: pending triage

Reference:

- [C:\JPop_Songwriter\AKIRA ENGINE\scripts\README.md](C:\JPop_Songwriter\AKIRA ENGINE\scripts\README.md)

## Configuration

Environment and local config guidance:

- [C:\JPop_Songwriter\AKIRA ENGINE\config\README.md](C:\JPop_Songwriter\AKIRA ENGINE\config\README.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\config\.env.example](C:\JPop_Songwriter\AKIRA ENGINE\config\.env.example)

Typical environment variables:

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`

## Documentation Map

Start here:

- [C:\JPop_Songwriter\AKIRA ENGINE\docs\README.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\README.md)

Important current docs:

- [C:\JPop_Songwriter\AKIRA ENGINE\docs\cli-skeleton.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\cli-skeleton.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\active-workflow.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\active-workflow.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\professional-song-quality-target.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\professional-song-quality-target.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\low-value-data-policy.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\low-value-data-policy.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\akira-supervised-training-schema.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\akira-supervised-training-schema.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\training-data-shaping.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\training-data-shaping.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\rights-cleared-training-corpus.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\rights-cleared-training-corpus.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\autonomous_execution_doctrine.md](C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\autonomous_execution_doctrine.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\one_week_execution_plan.md](C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\one_week_execution_plan.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\one_week_execution_runbook.md](C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\one_week_execution_runbook.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\one_week_success_metrics.md](C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\one_week_success_metrics.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\ten_hour_execution_plan.md](C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\ten_hour_execution_plan.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\ten_hour_execution_runbook.md](C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\ten_hour_execution_runbook.md)
- [C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\ten_hour_fallback_ladders.md](C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\ten_hour_fallback_ladders.md)

## Dependency Install

```powershell
pip install -r requirements.txt
```

## Rebuild Rule

If a workflow needs to be kept, prefer this order:

1. implement or move logic into `src/akira_engine/`
2. expose it through `src/akira_engine/cli/`
3. wire it into `akira.py`
4. keep a `scripts/` shim only if external compatibility still matters
