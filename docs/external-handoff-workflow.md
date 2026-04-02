# External Handoff Workflow

## Purpose

Prepare active conditioning tracks for external full-grounding work, validate returned JSON, then merge it into canonical records.

## Build Handoff Manifest

```powershell
python scripts/pipeline/build_external_handoff.py `
  --artist-id pinocchiop `
  --project-root C:\JPop_Songwriter\AKIRA ENGINE

python scripts/pipeline/build_external_handoff.py `
  --artist-id deco27 `
  --project-root C:\JPop_Songwriter\AKIRA ENGINE
```

Outputs:

- `data/_global/external_handoff/<artist_id>/handoff_manifest.json`
- `data/_global/external_handoff/<artist_id>/handoff_manifest.md`
- `data/_global/external_handoff/<artist_id>/incoming/`

## Validate Returned JSON

```powershell
python scripts/pipeline/validate_external_conditioning.py `
  --artist-id deco27 `
  --input-dir C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\deco27\incoming `
  --project-root C:\JPop_Songwriter\AKIRA ENGINE
```

Validation currently checks:

- `track_id` present
- `lyric_sources` present
- `metadata_sources` present
- `lyric_ground_truth.full_text_status = full`
- at least 5 grounded lyric sections
- at least 2 hook lines
- at least 5 `section_analysis` entries

## Merge After Validation

```powershell
python scripts/pipeline/merge_external_conditioning.py `
  --artist-id deco27 `
  --input-dir C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\deco27\incoming `
  --project-root C:\JPop_Songwriter\AKIRA ENGINE `
  --backup
```

## Re-audit

```powershell
python scripts/pipeline/audit_conditioning_records.py `
  --artist-id deco27 `
  --project-root C:\JPop_Songwriter\AKIRA ENGINE `
  --active-queue-only

python scripts/pipeline/report_engine_health.py
```
