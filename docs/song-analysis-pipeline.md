# Song Analysis Pipeline

This pipeline turns one reference song into reusable songwriting data.

It is not a manual five-round note-taking process. It is a runnable pipeline that loads inputs, writes pass outputs, validates claims, and emits both a human report and AI reconstruction JSON.

## Commands

Scrape Vocaloid song metadata from VocaDB and create per-track input packages:

```powershell
python akira.py song-analysis scrape-vocadb `
  --metadata-output-dir outputs/song_scrape/vocadb_metadata `
  --output-root outputs/song_scrape/song_inputs `
  --page-count 1 `
  --page-size 50
```

This command does not scrape lyric text. It writes `song_input.json`, `audio_features.json`, `source_manifest.json`, and `lyrics.todo.txt` for each collected track.

If locally obtained lyric files are available, attach them while materializing packages:

```powershell
python akira.py song-analysis materialize-metadata `
  --metadata-dir outputs/song_scrape/vocadb_metadata `
  --output-root outputs/song_scrape/song_inputs `
  --lyrics-root C:/path/to/local_lyrics `
  --overwrite
```

`lyrics-root` matches files by `track_id.txt`, exact title, or normalized title. Only matched local files become `lyrics.txt` and are marked ready for analysis.

Create a runnable input template:

```powershell
python akira.py song-analysis init-template --output-dir inputs/song_analysis/my_song --song-id my_song
```

Run analysis:

```powershell
python akira.py song-analysis run --input-dir inputs/song_analysis/my_song --output-dir outputs/song_analysis/my_song
```

## Inputs

Required:

- `song_input.json`
- `lyrics.txt`

Optional:

- `timeline_manual.json`
- `audio_features.json`
- `transcript.json`

Scraped metadata packages are analysis-ready only after `lyrics.txt` exists. Packages with `lyrics.todo.txt` are acquisition records, not analysis inputs.

## Passes

1. `pass_1_identity.json`
   - core identity, surface mood, hidden mood, speaker type, core conflict

2. `pass_2_lyrics.json`
   - section and line-level lyric function analysis

3. `pass_3_timeline.json`
   - timeline or inferred section-flow analysis

4. `pass_4_music_hooks.json`
   - composition, arrangement, rhythm, and hook mechanism analysis

5. `pass_5_recipe.json`
   - integrated songwriting formula and reuse strategy

Final outputs:

- `human_report.md`
- `ai_reconstruction.json`
- `validation_report.json`
- `run_manifest.json`

## Claim Rule

Every reusable analysis claim must follow this shape:

```text
choice -> reason -> effect -> reuse_method -> evidence -> confidence -> status
```

Statuses:

- `VERIFIED`: official or supplied metadata
- `OBSERVED`: directly visible in lyrics, timeline, or audio features
- `INFERRED`: reasoned from evidence
- `HYPOTHESIS`: plausible but not confirmed

## Validation Rules

The validator blocks outputs when:

- a claim lacks `choice`, `reason`, `effect`, `reuse_method`, `status`, or `confidence`
- `INFERRED` or `HYPOTHESIS` claims have no evidence
- confidence is outside `0..1`
- line-level lyric analysis is missing
- timeline sections lack intent or listener effect
- final recipe lacks `must_keep`, `can_change`, or `avoid`

## Current Limit

The first implementation uses deterministic heuristics. It gives the project a stable data contract and runnable pipeline first.

The next improvement should plug in stronger analyzers for:

- official metadata verification
- audio-derived section markers
- hook similarity and repeated phrase mining
- Japanese phonetic/rhyme analysis
- cross-song recipe comparison
