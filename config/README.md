# Config Skeleton

This directory is intentionally reduced to a clean skeleton.

Rules:

- Do not commit live secrets here.
- Keep only templates or placeholder config files.
- Put machine-local secrets in files that stay outside the active rebuild workspace.

Use:

- `.env.example` for environment variable names only
- `active_workflow.json` for the current workflow contract and validation targets

Validate:

```powershell
python akira.py workflow validate
```

Previous live config was moved to:

- `C:\JPop_Songwriter\AKIRA ENGINE\_quarantine\2026-04-03\quarantine\config`
