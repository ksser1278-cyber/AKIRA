# Songwriter Surface

`akira.py` is the primary entrypoint.

Active `scripts/songwriter/` is reduced to a single compatibility shim:

- `run_demo_songwriter.py`

This shim delegates to:

- `C:\JPop_Songwriter\AKIRA ENGINE\src\akira_engine\cli\songwriter_commands.py`

## Internalized Coverage

- `akira.py songwriter demo`

## Stage 5 Quarantine

Legacy songwriter scripts were moved out of the active rebuild surface.

Location:

- `C:\JPop_Songwriter\AKIRA ENGINE\_quarantine\2026-04-03\songwriter_stage5`

## Rule

Do not add new user-facing songwriter commands here first.

Add them to `akira.py` and `src/akira_engine/cli/` first, then keep a shim only if external compatibility still matters.
