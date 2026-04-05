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

If the project moves into supervised tuning, use a separate final export contract instead of reusing the intermediate records directly:

- [akira-supervised-training-schema.md](/C:/JPop_Songwriter/AKIRA%20ENGINE/docs/akira-supervised-training-schema.md)
- [akira_supervised_training_sample.schema.json](/C:/JPop_Songwriter/AKIRA%20ENGINE/schemas/akira_supervised_training_sample.schema.json)
- [lyric-technique-extraction-fields.md](/C:/JPop_Songwriter/AKIRA%20ENGINE/docs/lyric-technique-extraction-fields.md)
- [lyric_technique_record.schema.json](/C:/JPop_Songwriter/AKIRA%20ENGINE/schemas/lyric_technique_record.schema.json)

That final layer should sit after `derived_training_record` generation and after rights filtering.

Recommended long-term data flow:

1. `reference_corpus`
2. `lyric_technique_record`
3. `track_generation_record`
4. `derived_training_record`
5. `akira_supervised_training_sample`

For Vocaloid catalog work, metadata collection may rely on specialist databases such as VocaDB or Vocaloid Wiki, but those references should stay in metadata-support fields and not be treated as lyric-training clearance on their own.

For future Suno-oriented packaging, the corpus also needs a sound-intelligence layer rather than lyric-only technique extraction. That layer should be captured in:

- [sound-profile-field-set.md](/C:/JPop_Songwriter/AKIRA%20ENGINE/docs/sound-profile-field-set.md)
- [track_generation_record.schema.json](/C:/JPop_Songwriter/AKIRA%20ENGINE/schemas/track_generation_record.schema.json)
- [suno-prompt-asset-schema.md](/C:/JPop_Songwriter/AKIRA%20ENGINE/docs/suno-prompt-asset-schema.md)
- [suno_prompt_asset.schema.json](/C:/JPop_Songwriter/AKIRA%20ENGINE/schemas/suno_prompt_asset.schema.json)

That means the long-term flow is no longer only:

- metadata -> lyric technique -> training

It should become:

- metadata -> lyric technique + sound profile -> generation profile -> training and prompt packaging

Current blocker:

- metadata-derived `track_generation_record` corpora and existing `lyric_technique_record` corpora do not yet share a common `track_id` space
- direct merge is therefore blocked until the project builds technique extraction on the same canonical metadata track universe or introduces an explicit id mapping layer

Use this audit command to confirm whether a generation corpus and technique corpus can be merged directly:

```powershell
python akira.py dataset audit-generation-joinability --project-root . --generation-jsonl datasets\training\generation_profiles\tier2_batch9_probe_v2\track_generation_records.jsonl --technique-jsonl datasets\training\technique_probe_v3\lyric_technique_records.jsonl
```

If you want to iterate on one artist first, build a focused package:

```powershell
python build_artist_training_package.py `
  --artist-id ado `
  --project-root . `
  --audit-json reports/quality/corpus_audit.json
```

That writes a compact artist-only package under `datasets/training/<artist_id>/` plus a short readiness report in `reports/quality/`.
