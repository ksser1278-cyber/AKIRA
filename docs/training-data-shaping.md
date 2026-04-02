# Training Data Shaping

The project should avoid jumping straight from scraped lyrics to direct lyric fine-tuning. A more robust path is:

1. scrape and normalize the corpus
2. analyze track and artist patterns
3. audit corpus quality
4. convert only eligible tracks into non-verbatim training records

Build the derived datasets like this:

```powershell
python build_training_datasets.py `
  --project-root . `
  --audit-json reports/quality/corpus_audit.json `
  --minimum-recommendation needs_review
```

Default outputs:

- `datasets/training/track_blueprints.jsonl`
- `datasets/training/artist_style_cards.jsonl`
- `datasets/training/training_manifest.json`

Why these datasets exist:

- `track_blueprints.jsonl`
  - one record per eligible track
  - stores derived structure, imagery, emotion, and hook evidence
  - does not store verbatim commercial lyrics in the training target

- `artist_style_cards.jsonl`
  - one record per eligible artist
  - stores reusable retrieval-time conditioning summaries
  - works well as RAG or prompt-context material

This gives the project a safer and more controllable intermediate dataset layer before deciding whether to train a model, build a planner, or use retrieval-first generation.

If you want to iterate on one artist first, build a focused package:

```powershell
python build_artist_training_package.py `
  --artist-id ado `
  --project-root . `
  --audit-json reports/quality/corpus_audit.json
```

That writes a compact artist-only package under `datasets/training/<artist_id>/` plus a short readiness report in `reports/quality/`.
