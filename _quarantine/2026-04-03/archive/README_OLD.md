# AKIRA ENGINE

AKIRA ENGINE is a Vocaloid / subculture songwriting workspace for building conditioning corpora, lyric-generation datasets, SUNO.AI-ready song packages, and reusable style blueprints.

The long-term goal is not a single monolithic model. The real target is a repeatable pipeline:

1. Collect lyric files safely and consistently.
2. Normalize them into machine-readable documents.
3. Analyze subculture style signals from anchor tracks.
4. Derive draft style profiles and mode taxonomies from that evidence.
5. Turn that knowledge into datasets, blueprints, external-generation request bundles, and SUNO song packages.
6. Score outputs against style rules and reuse the corpus for future tuning or retrieval.

The primary reference axis is now:

- `PinocchioP`
- `DECO*27`

See [docs/vocaloid-subculture-pivot.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\vocaloid-subculture-pivot.md).
See [docs/vocaloid-anchor-set.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\vocaloid-anchor-set.md).
See [docs/vocaloid-conditioning-workflow.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\vocaloid-conditioning-workflow.md).

## Current MVP

This repository now includes:

- a local lyric ingestion and normalization pipeline
- a web lyric scraping pipeline from user-supplied URLs
- a track and artist lyric analysis pipeline
- a draft profile derivation step from artist analysis
- a post-collection corpus audit for training readiness
- a track-intent enrichment step so songs carry purpose and tie-in metadata
- a manual reference-track dossier layer for gold-grade song-intent evidence
- an auto-built track dossier layer that borrows the deep-analysis format for corpus records
- a machine-readable artist profile schema
- a structured sample profile for Ado
- a seed-driven JSONL dataset builder for lyric planning records
- a multi-artist dataset builder and corpus merger
- a derived training-data shaper for non-verbatim track blueprints and artist style cards
- an artist-focused training package builder for single-artist iteration
- an artist-focused experiment-set builder for task-by-task supervision
- an artist-focused eval-set builder for held-out benchmarking
- a deterministic eval benchmark runner for baseline generation and scoring
- a safe original lyric draft generator from abstracted brief records
- a standard-library Python generator that converts a profile into a SUNO package
- a unified `song package` pipeline that can export requests, run an external generator, score the result, and emit SUNO bundles
- project documentation that maps the MVP to the long-term model vision

## Canonical Structure

The repository has many historical scripts and archived outputs. The canonical structure going forward is:

- `artists/`
  - artist-level profiles, mode profiles, representative demo defaults
- `data/reference_tracks/`
  - high-signal anchor conditioning records
- `datasets/experiments/`
  - planner input JSONL built from conditioning records
- `src/akira_engine/`
  - core library modules only
- `scripts/pipeline/`
  - corpus-building and conditioning-building entrypoints
- `scripts/songwriter/`
  - planner, benchmark, and song-package entrypoints
- `scripts/eval/`
  - critic and benchmark scoring entrypoints
- `scripts/suno/`
  - SUNO bundle and prompt-pack tooling
- `outputs/`
  - current active runs
- `outputs/_archive/`
  - historical runs kept for comparison only

Operational rule:

- new benchmark baselines should live under `outputs/<artist_or_domain>/...`
- frozen historical baselines should move under `outputs/_archive/...`
- planning inputs should come from `datasets/experiments/...`, not ad-hoc JSON files
- reusable reference truth should live in `data/reference_tracks/...`, not `reports/...`

## Project Layout

```text
.agent/                     Workflow notes and automation configs
artists/                    Structured artist profiles and anchor workspaces
config/                     Local config and secrets (.env, API keys)
data/                       Reference tracks, audio, Spotify data, anchor sets
datasets/                   Training-ready JSONL outputs and eval sets
docs/                       Architecture, planning, and research docs
  archive/briefs/           Archived prompt briefs (GPT, Gemini, tri-counsel)
lyrics/                     Raw lyric sources, manifests, and normalized docs
outputs/                    Generated plans, scores, and SUNO song packages
  _archive/                 Archived experiment runs
  _loose/                   One-off generation outputs
reports/                    Quality reports, dossiers, discography, style
schemas/                    JSON schemas for machine-readable inputs
scripts/                    Pipeline, songwriter, dataset, eval, ingest, suno
src/akira_engine/           Core engine modules
```

## Canonical Entry Points

Use these as the default top-level commands. Everything else should be treated as support tooling or legacy.

### Build conditioning-driven planner inputs

```powershell
python scripts/pipeline/build_conditioning_brief_dataset.py `
  --artist-id pinocchiop `
  --project-root .
```

### Run a single songwriter benchmark case

```powershell
python scripts/songwriter/run_songwriter_v2.py `
  --source-jsonl datasets/experiments/pinocchiop/full_song_brief.jsonl `
  --track-id pinocchiop_kamippoi_na `
  --output-dir outputs/pinocchiop/songwriter_v2/pinocchiop_kamippoi_na
```

### Run an anchor benchmark set

```powershell
python scripts/songwriter/run_anchor_track_matrix.py `
  --artist-id pinocchiop `
  --source-jsonl datasets/experiments/pinocchiop/full_song_brief.jsonl `
  --output-dir outputs/pinocchiop/benchmarks
```

### Run the full song-package pipeline

```powershell
python scripts/songwriter/run_song_package_pipeline.py `
  --source-jsonl datasets/experiments/pinocchiop/full_song_brief.jsonl `
  --track-id pinocchiop_kamippoi_na `
  --output-dir outputs/song_package_pipeline/pinocchiop_kamippoi_na
```

## Engine Boundary

The engine is responsible for:

- conditioning records
- planner inputs
- song planning
- style prompt construction
- critic / rerank / benchmark
- SUNO package export

The engine is not the final sentence-level lyric writer. The preferred production path is:

1. conditioning record
2. planner
3. external generator
4. critic / rerank
5. SUNO bundle

## Quick Start

Normalize a local lyric source manifest first:

```powershell
python normalize_lyrics.py `
  --manifest lyrics/manifests/demo_manifest.json
```

Or scrape lyric pages from the web into raw files plus a generated manifest:

```powershell
python scrape_web_lyrics.py `
  --web-manifest lyrics/web/ado_sources.template.json `
  --overwrite
```

Or discover a whole artist discography manifest from UtaTen first:

```powershell
python discover_discography.py `
  --artist-id ado `
  --artist-name Ado `
  --site utaten `
  --artist-url https://utaten.com/artist/lyric/39156 `
  --request-delay-seconds 0.5
```

Then enrich and cross-check that discography with Spotify metadata:

```powershell
python fetch_spotify_discography.py --artist-name Ado
python compare_discography_coverage.py `
  --lyrics-manifest lyrics/manifests/ado_manifest.json `
  --spotify-discography data/spotify/ado_discography.json
```

If Spotify shows lyric-bearing originals that were missed by the automatic discovery pass, add them to a manual backfill manifest and rescrape:

```powershell
python scrape_web_lyrics.py `
  --web-manifest lyrics/web/ado_manual_backfill.utaten.json

python compare_discography_coverage.py `
  --lyrics-manifest lyrics/manifests/ado_manifest.merged.json `
  --spotify-discography data/spotify/ado_discography.json `
  --output reports/discography/ado_coverage.merged.md
```

Then build the lyric blueprint dataset from the sample Ado profile:

```powershell
python build_dataset.py `
  --artist artists/ado/profile.json `
  --seeds artists/ado/seeds.json
```

To derive a draft profile from analyzed lyric evidence:

```powershell
python analyze_lyrics.py
python aggregate_artist_analysis.py
python render_analysis_report.py --artist-analysis lyrics/analyzed/artists/demo.json
python derive_artist_profile.py --analysis lyrics/analyzed/artists/demo.json
```

For a real artist workflow, drop lyric files into `lyrics/raw/<artist_id>/` and run the full pipeline in one command:

```powershell
python run_artist_pipeline.py `
  --artist-id ado `
  --artist-name Ado `
  --raw-dir lyrics/raw/ado
```

This auto-generates `lyrics/manifests/ado_manifest.json` from the raw files, then runs normalization, track analysis, artist aggregation, style reporting, and draft profile derivation.

For a web-first workflow, scrape and run the full pipeline in one command:

```powershell
python run_artist_pipeline.py `
  --web-manifest lyrics/web/ado_sources.template.json `
  --overwrite-web
```

Build all per-artist datasets and merge them into one corpus:

```powershell
python build_all_datasets.py
python build_corpus.py
```

Run the full scraping flow for multiple artists from one registry:

```powershell
python bulk_scrape_artists.py `
  --registry lyrics/bulk/artist_registry.template.json `
  --project-root . `
  --overwrite
```

Audit the scraped corpus before using it for training:

```powershell
python audit_corpus.py `
  --project-root .
```

Promote curated tracks into intent cards that capture what each song is trying to do:

```powershell
python scripts/pipeline/build_track_intent_cards.py `
  --artist-id ado `
  --project-root .
```

See `docs/track-intent.md`.

For deeper, manual song-purpose references that capture arrangement intent and section-level dramatic function:

- `docs/reference-track-dossiers.md`
- `data/reference_tracks/pinocchiop/bokunankaiinakutemo.intent.json`

To convert corpus tracks into richer dossier records that follow the same shape:

```powershell
python scripts/pipeline/build_track_dossiers.py `
  --artist-id ado `
  --project-root .
```

See `docs/track-dossiers.md`.

Convert audited artists into derived training datasets:

```powershell
python build_training_datasets.py `
  --project-root . `
  --audit-json reports/quality/corpus_audit.json `
  --minimum-recommendation needs_review
```

Build a focused single-artist package when you want to iterate deeply on one artist first:

```powershell
python build_artist_training_package.py `
  --artist-id ado `
  --project-root . `
  --audit-json reports/quality/corpus_audit.json
```

Split that package into smaller experiment tasks:

```powershell
python build_artist_experiment_sets.py `
  --artist-id ado `
  --project-root .
```

Build held-out eval sets from the same artist package:

```powershell
python build_artist_eval_sets.py `
  --artist-id ado `
  --project-root .
```

Run a baseline benchmark over those held-out eval files:

```powershell
python run_artist_eval_benchmark.py `
  --artist-id ado `
  --project-root .
```

Score an external prediction directory against the same held-out eval files:

```powershell
python score_artist_eval_predictions.py `
  --artist-id ado `
  --project-root . `
  --predictions-dir datasets/eval_runs/ado/heuristic_baseline_v1/predictions
```

Render a readable original lyric draft from a held-out or experiment brief:

```powershell
python generate_lyric_draft.py `
  --source-jsonl datasets/evals/ado/full_song_brief_eval.jsonl `
  --track-id utaten_hw22011303
```

Run the newer stage-by-stage songwriting pipeline instead of the old single-pass renderer:

```powershell
python run_songwriter_v2.py `
  --source-jsonl datasets/experiments/ado/full_song_brief.jsonl `
  --track-id utaten_hw22011303 `
  --candidate-count 6
```

This writes a structured song plan, an LLM-ready prompt package, multiple candidates, critic scores, and the selected best draft under `outputs/songwriter_v2/`.

Run the full song package pipeline from planner to external generation to SUNO bundle:

```powershell
python scripts\songwriter\run_song_package_pipeline.py `
  --source-jsonl datasets\experiments\ado\full_song_brief.jsonl `
  --track-id utaten_hw22011303 `
  --external-mode export-only
```

Or run the same path through Gemini directly:

```powershell
python scripts\songwriter\run_song_package_pipeline.py `
  --source-jsonl datasets\experiments\ado\full_song_brief.jsonl `
  --track-id utaten_hw22011303 `
  --external-mode gemini `
  --min-score 85
```

See [docs/song-package-pipeline.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\song-package-pipeline.md).

Run that same pipeline over a diverse subset of tracks:

```powershell
python run_songwriter_v2_batch.py `
  --source-jsonl datasets/experiments/ado/full_song_brief.jsonl `
  --count 12 `
  --candidate-count 6
```

Score external model outputs against the stored Songwriter V2 plans:

```powershell
python score_songwriter_v2_predictions.py `
  --run-root outputs/songwriter_v2/ado `
  --predictions-dir outputs/songwriter_v2_external_test
```

Export a whole Songwriter V2 run root as model-ready request JSONL:

```powershell
python export_songwriter_v2_requests.py `
  --run-root outputs/songwriter_v2_batch_test `
  --output-dir outputs/songwriter_v2_request_bundle
```

Import model response JSONL back into markdown files before scoring:

```powershell
python import_songwriter_v2_predictions.py `
  --input-jsonl outputs/songwriter_v2_request_bundle/sample_predictions.jsonl `
  --output-dir outputs/songwriter_v2_imported_predictions
```

Run the exported requests directly through Gemini with automatic response validation and retry:

```powershell
python run_gemini_songwriter_requests.py `
  --requests-jsonl outputs/songwriter_v2_request_bundle/requests.jsonl `
  --project-root . `
  --output-dir outputs/gemini_songwriter_run `
  --retry-attempts 4 `
  --max-output-tokens 3072
```

Run the full Songwriter V2 -> Gemini -> import -> score roundtrip in one command:

```powershell
python run_gemini_songwriter_roundtrip.py `
  --run-root outputs/songwriter_v2_batch_v2_test `
  --project-root . `
  --work-dir outputs/gemini_songwriter_roundtrip `
  --score-dir reports/quality/gemini_songwriter_roundtrip `
  --retry-attempts 4 `
  --max-output-tokens 3072
```

Run a critic-guided revision pass only for low-scoring tracks from an existing scoring manifest:

```powershell
python run_gemini_songwriter_revision_roundtrip.py `
  --scoring-manifest reports/quality/gemini_songwriter_roundtrip_v2_holdout20/scoring_manifest.json `
  --project-root . `
  --work-dir outputs/gemini_songwriter_revision_holdout20 `
  --score-dir reports/quality/gemini_songwriter_revision_holdout20 `
  --score-threshold 88 `
  --max-revisions 8
```

Build a gold-review bundle from strong outputs so a human can approve real keeper lyrics:

```powershell
python build_goldset_review_bundle.py `
  --scoring-manifest reports/quality/gemini_songwriter_roundtrip_v2_holdout20/scoring_manifest.json `
  --output-dir datasets/goldset_review/ado_holdout20 `
  --min-score 90 `
  --max-records 10
```

Build pairwise preference packets from two systems on the same tracks:

```powershell
python build_preference_bundle.py `
  --left-scoring-manifest reports/quality/gemini_songwriter_roundtrip_v2_holdout20/scoring_manifest.json `
  --right-scoring-manifest reports/quality/gemini_songwriter_revision_holdout20/scoring_manifest.json `
  --left-label gemini_validated `
  --right-label gemini_revision `
  --output-dir datasets/preference_review/ado_revision_vs_validated `
  --max-pairs 8
```

Rewrite only the weakest section of low-scoring tracks and merge it back into the full lyric:

```powershell
python run_gemini_songwriter_section_rewrite_roundtrip.py `
  --scoring-manifest reports/quality/gemini_songwriter_roundtrip_v2_holdout20/scoring_manifest.json `
  --project-root . `
  --work-dir outputs/gemini_songwriter_section_rewrite_holdout20 `
  --score-dir reports/quality/gemini_songwriter_section_rewrite_holdout20 `
  --score-threshold 87.5 `
  --max-tracks 6 `
  --sections-per-track 1
```

Build final SUNO-ready song packages that pair a style prompt with full lyrics:

```powershell
python build_suno_song_bundle.py `
  --scoring-manifest reports/quality/gemini_songwriter_roundtrip_v2_holdout20/scoring_manifest.json `
  --output-dir outputs/suno_song_bundle/ado_holdout20 `
  --min-score 90 `
  --max-records 5
```

Each bundle now includes:

- a detailed natural-language style prompt for Suno Custom mode
- a shorter tag-style backup prompt
- an `Exclude Styles` string
- lyric-box guidance with an optional context header
- slider guidance for `Style Influence`, `Weirdness`, `Prompt Influence`, and `Prompt Boost`
- workflow tips for `Replace Section`, `Persona`, `Inspire`, and `Add Vocals`

See `docs/suno-prompting.md` for official-aligned prompting rules, `docs/suno-community-tips.md` for user-discovered workflow tips, and `docs/style-prompt-content.md` for the content-selection layer behind the style prompt itself.

To inspect mode-by-mode style prompt content even before you have full scored song bundles for each mode:

```powershell
python build_style_prompt_mode_probes.py `
  --profile artists/ado/style_prompt_profile.json `
  --output-dir outputs/style_prompt_probes/ado
```

To turn bundles or mode probes into a real Suno listening-test pack:

```powershell
python build_suno_ab_test_pack.py `
  --source-dir outputs/suno_song_bundle/ado_promptclean88/json `
  --output-dir outputs/suno_ab_packs/ado_promptclean88
```

See `docs/suno-ab-testing.md` for the manual listening workflow. The default comparison is now `balanced_detailed` vs `minimal_core`.

Generate a single SUNO package from the same profile:

```powershell
python generate_prompt_package.py `
  --artist artists/ado/profile.json `
  --mode rock_rebellion `
  --theme "pressure and rebellion" `
  --emotion "defiant" `
  --narrative "A masked narrator breaks out of social pressure at midnight."
```

The dataset output will be written to `datasets/processed/`.

The markdown package output will be written to `outputs/`.

Curate normalized lyrics before treating them as training candidates:

```powershell
python scripts/pipeline/curate_lyrics_corpus.py `
  --artist-id ado `
  --project-root .
```

See `docs/lyric-curation.md`.

## Web Scraping Notes

- The scraper expects user-supplied lyric page URLs instead of broad web crawling.
- It respects `robots.txt` by default.
- UtaTen and PetitLyrics worked in live preset checks; Uta-Net preset exists but may be blocked by `robots.txt`.
- `discover_discography.py` can generate a full Ado-style web manifest from a supported artist lyric page.
- `lyrics/web/ado_manual_backfill.utaten.json` is the place for hand-found lyric-bearing gaps that Spotify coverage uncovers.
- If auto extraction is noisy, add a page selector in the web manifest.
- `compare_discography_coverage.py` now separates lyric-bearing works from redundant remix or instrumental variants so dataset coverage is easier to judge.
- `bulk_scrape_artists.py` batches discovery, scraping, Spotify coverage checks, secondary backfill, and manual backfill from one registry file.
- `audit_corpus.py` scores scraped artists and tracks for post-collection training readiness.
- `build_training_datasets.py` converts audited corpora into non-verbatim learning records for planning and retrieval.
- `build_artist_training_package.py` builds a compact per-artist package for focused experimentation.
- `build_artist_experiment_sets.py` splits one artist package into reusable task-specific instruction sets.
- `build_artist_eval_sets.py` creates held-out eval files with rubrics for benchmarking those task sets.
- `run_artist_eval_benchmark.py` generates deterministic baseline predictions and scores them against the held-out eval sets.
- `score_artist_eval_predictions.py` scores any compatible prediction directory against the same held-out eval sets.
- `generate_lyric_draft.py` renders an original lyric draft from abstracted brief records without direct artist imitation.
- See `docs/web-scraping.md` for the full workflow.
- See `docs/bulk-scraping.md` for the multi-artist batch workflow.
- See `docs/corpus-audit.md` for quality audit rules.
- See `docs/training-data-shaping.md` for the post-audit dataset strategy.
- See `docs/artist-experiment-sets.md` for the Ado-first experiment workflow.
- See `docs/artist-eval-sets.md` for held-out benchmarking.
- See `docs/artist-eval-benchmark.md` for the first executable benchmark loop.
- See `docs/lyric-draft-generation.md` for the original lyric draft step.

## Why This Matters

The markdown files in `data/` are useful for humans, but they are hard to automate against. The ingestion and schema-backed paths give us a bridge from lyric sources and research notes to deterministic generation and training-ready dataset rows.

The internal renderer is no longer treated as the final lyric engine. The project now assumes:

- `AKIRA ENGINE` owns planning, conditioning, scoring, and bundling
- an external generator supplies the final lyric sentences
- the benchmark set decides whether the external result is good enough

## Next Milestones

- build the first `PinocchioP + DECO*27` 20-track anchor set
- define `ironic_meta`, `direct_emotional_pop`, and `dark_cute_breakdown` mode rules
- move benchmark focus from Ado to Vocaloid / subculture reference tracks
- validate the external generation path against the new benchmark set
