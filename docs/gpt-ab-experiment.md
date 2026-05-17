# GPT Direct vs AKIRA-Assisted Experiment

This workflow treats GPT direct generation as the baseline.

AKIRA-assisted generation must be grounded in collected AKIRA analysis outputs. It must not invent plausible-looking guidance by itself.

AKIRA is useful only when a data-grounded assisted prompt beats the direct prompt under the same task. If the assisted result is worse, the analysis data, prompt compiler, or selection rule should be revised or removed.

## Prompt-Only Run

```powershell
python akira.py songwriter ab-test `
  --intent "two-faced cute cyber idol song about a notification that lies" `
  --style "Japanese Vocaloid/NicoNico subculture pop-rock, synthetic vocal, sharp hook" `
  --title-seed "Ping Lie" `
  --output-dir outputs/gpt_ab/ping_lie
```

This writes:

- `direct_prompt.md`
- `direct_request.json`
- `ab_manifest.json`
- `ab_report.md`

Without `--analysis-dir`, this is direct-baseline prompt generation only. No assisted prompt is created.

## Use Song Analysis Data

```powershell
python akira.py songwriter ab-test `
  --intent "make an original toxic-cute Vocaloid song" `
  --style "bright synthetic pop-rock with unstable character hook" `
  --analysis-dir outputs/song_analysis/reference_song `
  --output-dir outputs/gpt_ab/reference_assisted
```

The assisted prompt uses sanitized analysis summaries from:

- `ai_reconstruction.json`
- `pass_5_recipe.json`

It does not inject source lyric lines.

If `--analysis-dir` is missing or too sparse, assisted generation is blocked.

## Compare External Outputs

If results were generated in ChatGPT or another UI:

```powershell
python akira.py songwriter ab-test `
  --intent "same task" `
  --style "same style" `
  --analysis-dir outputs/song_analysis/reference_song `
  --direct-output-path outputs/gpt_ab/manual/direct.md `
  --assisted-output-path outputs/gpt_ab/manual/assisted.md `
  --output-dir outputs/gpt_ab/manual_compare
```

This writes `comparison.json` with:

- `direct` scores
- `assisted` scores
- `assisted_minus_direct`
- `verdict`

The comparison is heuristic. It is a regression signal, not final artistic judgment.

## API Execution

```powershell
python akira.py songwriter ab-test `
  --intent "same task" `
  --style "same style" `
  --analysis-dir outputs/song_analysis/reference_song `
  --output-dir outputs/gpt_ab/api_run `
  --execute-api
```

Requires `OPENAI_API_KEY` in the environment or `config/.env`.

## Decision Rule

Keep an AKIRA method only if it repeatedly improves GPT direct output.

Do not count ungrounded assisted prompts as AKIRA evidence.

Remove or rewrite it if it causes:

- lower hook force
- lower premise specificity
- stiff sectioning
- generic Vocaloid cliches
- excessive repetition
- less usable Suno style prompts
