# CLI Skeleton

## Purpose

`akira.py` is the new single entrypoint for the reduced rebuild workspace.

It does not replace every legacy script yet.
It defines the new execution surface first.

## Current Commands

### Status

```powershell
python akira.py status
```

### Songwriter Demo

```powershell
python akira.py songwriter demo --artist-id maretu --mode-id dark_cute_breakdown
```

### Derived Training Dataset Build

```powershell
python akira.py dataset build-derived --project-root .
```

### Technique Extraction

```powershell
python akira.py dataset extract-technique-records --project-root .
```

This command extracts intermediate `lyric_technique_record` rows from normalized lyric corpora. In the reduced rebuild workspace it falls back to archived lyric corpora when active lyric inputs are absent.

Owned-original extraction is also supported:

```powershell
python akira.py dataset extract-technique-records --project-root . --source-kind owned_original_hook_pilot --artists akira_original
```

Use `--source-kind normalized_corpus` for archived or active normalized lyric corpora, and `--source-kind owned_original_hook_pilot` for the rights-cleared hook pilot intake.

If active lyric-analysis inputs are missing, this command hydrates the derived dataset from archived JSONL assets under:

- `C:\JPop_Songwriter\AKIRA ENGINE\_quarantine\2026-04-03\archive`

### Rights Bootstrap

```powershell
python akira.py dataset bootstrap-rights --project-root .
```

### Track Generation Profiles

```powershell
python akira.py dataset build-track-generation-records --project-root . --corpus-root datasets\_global\vocaloid_metadata_canonical\tier2_batch9 --output-root datasets\training\generation_profiles\tier2_batch9
```

This command converts canonical Vocaloid metadata into `track_generation_record` rows. If a `lyric_technique_record` JSONL is supplied, it merges lyric-side structure and hook evidence into the generation profile.

```powershell
python akira.py dataset build-track-generation-records --project-root . --corpus-root datasets\_global\vocaloid_metadata_canonical\tier2_batch9 --output-root datasets\training\generation_profiles\tier2_batch9 --lyric-technique-jsonl datasets\training\technique_probe_v3\lyric_technique_records.jsonl
```

### Suno Prompt Assets

Default export is `ready only`.

```powershell
python akira.py dataset export-suno-prompt-assets --project-root . --generation-root datasets\training\generation_profiles\tier2_batch9
```

To materialize metadata-only prompt assets for downstream editing or review, include blocked records explicitly:

```powershell
python akira.py dataset export-suno-prompt-assets --project-root . --generation-root datasets\training\generation_profiles\tier2_batch9 --include-blocked
```

### Lyric Technique Acquisition Queue

```powershell
python akira.py dataset build-lyric-technique-acquisition-queue --project-root . --corpus-root datasets\_global\vocaloid_metadata_canonical\tier2_batch9 --output-root datasets\training\lyric_technique_acquisition_queue\tier2_batch9
```

This command materializes a `vocadb_*`-aligned acquisition queue for future lyric grounding and technique extraction. It is the bridge between canonical metadata collection and a future lyric-technique corpus that can actually merge with `track_generation_record`.

### VocaDB Lyric Grounding Workspace

```powershell
python akira.py dataset build-vocadb-lyric-grounding-workspace --project-root . --queue-root datasets\training\lyric_technique_acquisition_queue\tier2_batch9 --workspace-root datasets\_global\vocadb_lyric_grounding_acquisition\tier2_batch9
```

This command seeds a grounded-lyric workspace with `incoming/`, `accepted/`, `rejected/`, `needs_patch/`, `lyric_assets/`, and `section_maps/` while preserving the same `vocadb_*` ids used by canonical metadata.

### Import Grounded Technique Records

```powershell
python akira.py dataset import-vocadb-grounded-technique --project-root . --workspace-root datasets\_global\vocadb_lyric_grounding_acquisition\tier2_batch9 --output-root datasets\training\vocadb_grounded_technique\tier2_batch9
```

This command imports `accepted/` grounded lyric bundles into `lyric_technique_record` rows. It stays empty until accepted grounded bundles exist.

### Lyric Technique Pilot Cycle

```powershell
python akira.py dataset run-lyric-technique-pilot-cycle --project-root . --corpus-root datasets\_global\vocaloid_metadata_canonical\tier1_map_seed --workspace-root datasets\_global\vocadb_lyric_grounding_acquisition_pilots\tier1_map_seed_pilot10_v2
```

This command rebuilds generation profiles for the selected corpus, validates the pilot grounding workspace, imports any accepted grounded bundles, and reruns the joinability audit in one pass.

### Sound Profile Review Workspace

```powershell
python akira.py dataset build-sound-profile-review-workspace --project-root . --generation-root datasets\training\generation_profiles\tier1_map_seed_pilot10_merged_v10 --corpus-root datasets\_global\vocaloid_metadata_canonical\tier1_map_seed --output-root datasets\_global\sound_profile_review\tier1_map_seed_pilot10_v1
python akira.py dataset import-reviewed-sound-profiles --project-root . --generation-root C:\JPop_Songwriter\AKIRA ENGINE\datasets\training\generation_profiles\tier1_map_seed_pilot10_merged_v10 --workspace-root C:\JPop_Songwriter\AKIRA ENGINE\datasets\_global\sound_profile_review\tier1_map_seed_pilot10_v1 --output-root C:\JPop_Songwriter\AKIRA ENGINE\datasets\training\generation_profiles\tier1_map_seed_pilot10_sound_reviewed_v1
```

This lane keeps sound-profile review separate from lyric grounding. `incoming/` holds review templates for the current joined subset. Only `accepted/` review records upgrade `sound_profile_quality` to `reviewed`.

### Professional Quality Cycle

```powershell
python akira.py dataset run-professional-quality-cycle --project-root . --generation-root C:\JPop_Songwriter\AKIRA ENGINE\datasets\training\generation_profiles\tier1_map_seed_pilot10_merged_v10 --sound-review-workspace C:\JPop_Songwriter\AKIRA ENGINE\datasets\_global\sound_profile_review\tier1_map_seed_pilot10_v1 --reviewed-generation-root C:\JPop_Songwriter\AKIRA ENGINE\datasets\training\generation_profiles\tier1_map_seed_pilot10_sound_reviewed_v2 --readiness-output-root C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\generation_readiness_audit\tier1_map_seed_pilot10_sound_reviewed_v2 --prompt-asset-output-root C:\JPop_Songwriter\AKIRA ENGINE\datasets\training\suno_prompt_assets\tier1_map_seed_pilot10_sound_reviewed_v2
```

This command applies accepted sound-profile reviews, rebuilds the reviewed generation lane, reruns readiness audit, and refreshes prompt assets in one pass.

### Tier 1 Continuous Cycle

```powershell
python akira.py dataset run-tier1-continuous-cycle
```

This command runs the active Tier 1 loop in one pass:

- `pilot20` generation rebuild
- `pilot20` grounding validation
- `pilot20` grounded-technique import
- `pilot20` joinability audit
- `pilot10` sound-review workspace refresh
- reviewed generation rebuild
- readiness audit refresh
- grounding status refresh

### Program Continuous Cycle

```powershell
python akira.py dataset run-program-continuous-cycle --batch-tag 20260405_b --bulk-page-count 3 --bulk-page-size 50 --bulk-start-offset 150
```

This is the top-level continuous execution surface.
It runs:

- bulk VocaDB catalog intake
- review queue build
- triage and auto-accept
- canonicalization
- coverage, UTF-8, and value classification
- active Tier 1 continuous cycle

### Generation Joinability Audit

```powershell
python akira.py dataset audit-generation-joinability --project-root . --generation-jsonl datasets\training\generation_profiles\tier2_batch9_probe_v2\track_generation_records.jsonl --technique-jsonl datasets\training\technique_probe_v3\lyric_technique_records.jsonl
```

Use this command before attempting a direct merge between generation profiles and lyric-technique records.

### Vocaloid Metadata Seeding

```powershell
python akira.py dataset seed-vocadb-metadata --project-root . --queries "kanaria" "maretu"
```

This command calls the VocaDB public API and writes `vocaloid_metadata_record` seed files under:

- `datasets\_global\vocaloid_metadata_intake\incoming`

For producer-centered collection, prefer artist-based seeding:

```powershell
python akira.py dataset seed-vocadb-metadata --project-root . --artist-names "Kanaria" "MARETU"
```

For repeatable large-batch seeding, use an artist list file:

```powershell
python akira.py dataset seed-vocadb-metadata --project-root . --artist-list datasets\_global\vocaloid_metadata_intake\vocadb_artist_seed_list.txt
```

For deterministic Tier 1 seeding, prefer the explicit artist-id map:

```powershell
python akira.py dataset seed-vocadb-metadata --project-root . --artist-map datasets\_global\vocaloid_metadata_intake\vocadb_artist_seed_map.json
```

For catalog-scale intake without a producer list:

```powershell
python akira.py dataset seed-vocadb-bulk-metadata --project-root . --page-count 10 --page-size 50 --start-offset 0
```

Then run automatic canonical review:

```powershell
python akira.py dataset enrich-vocaloid-metadata --project-root .
python akira.py dataset review-vocaloid-metadata --project-root .
```

Then materialize the manual review queue:

```powershell
python akira.py dataset build-vocaloid-review-queue --project-root .
```

Then apply queue automation:

```powershell
python akira.py dataset auto-triage-vocaloid-queue --project-root .
python akira.py dataset auto-accept-vocaloid-queue --project-root .
python akira.py dataset build-vocaloid-canonical-corpus --project-root .
```

### Reports

```powershell
python akira.py report engine-health
python akira.py report baseline
```

### Supervised Export

Default is hook-only export.

```powershell
python akira.py dataset export-supervised --project-root . --rights-map datasets\\_global\\training_rights_map.json
```

Full-song export must be explicit:

```powershell
python akira.py dataset export-supervised --project-root . --rights-map datasets\\_global\\training_rights_map.json --include-full-song
```

Current expected behavior in the reduced rebuild workspace:

- derived dataset can be hydrated from archive
- supervised export may still produce `0` samples if all rights statuses remain blocked or unknown

### Tests

```powershell
python akira.py test
```

## Scope Rule

New functionality should be added to `akira.py` first.

Legacy scripts may remain as implementation targets, but they should stop being the primary user-facing entrypoints.

## Current Internalization Status

Already internalized behind `akira.py` and `src/akira_engine/cli/`:

- songwriter demo
- dataset build-derived
- dataset extract-technique-records
- dataset bootstrap-rights
- dataset export-supervised
- dataset build-track-generation-records
- dataset export-suno-prompt-assets
- dataset build-lyric-technique-acquisition-queue
- dataset build-vocadb-lyric-grounding-workspace
- dataset import-vocadb-grounded-technique
- dataset run-lyric-technique-pilot-cycle
- dataset audit-generation-joinability
- dataset import-training-sources
- dataset build-training-pilot
- dataset export-vertex-supervised
- report engine-health
- report baseline

## Rights-Cleared Intake Bridge

```powershell
python akira.py dataset import-training-sources --project-root .
```

This command reads accepted `owned_original_hook_pilot` records, updates `datasets\_global\training_rights_map.json`, and emits a small hook-generation supervised export under `datasets\training\owned_original_supervised`.

## Pilot Training Bundle

```powershell
python akira.py dataset build-training-pilot --project-root .
```

This command takes the raw eligible owned-original supervised samples and produces a small train/eval bundle under `datasets\training\pilots\owned_original_hook_v1`.

## Vertex AI Export

```powershell
python akira.py dataset export-vertex-supervised --project-root .
```

This command converts the pilot `train.jsonl` and `eval.jsonl` into Vertex AI Gemini supervised-tuning JSONL files and writes a stub `vertex_job_template.json`.
## Lyric Grounding Expansion

- `python akira.py dataset build-lyric-technique-pilot-batch`
  - supports `--exclude-track-ids` so the next pilot batch can be selected without reusing already accepted tracks
- `python akira.py dataset materialize-lyric-technique-pilot-workspace`
  - copies the selected pilot subset out of the full grounding workspace
- `python akira.py dataset run-lyric-technique-pilot-cycle`
  - builds the baseline generation profile, validates the workspace, imports accepted grounded bundles, and audits joinability
