# Artist Eval Benchmark

Once held-out eval sets exist, run a baseline benchmark so the evaluation loop is real before connecting a larger model.

Example:

```powershell
python run_artist_eval_benchmark.py `
  --artist-id ado `
  --project-root .
```

Default output:

- `datasets/eval_runs/<artist_id>/heuristic_baseline_v1/predictions/*.jsonl`
- `datasets/eval_runs/<artist_id>/heuristic_baseline_v1/scores/*.jsonl`
- `datasets/eval_runs/<artist_id>/heuristic_baseline_v1/benchmark_manifest.json`
- `reports/quality/<artist_id>_eval_benchmark.md`

What this run does:

- reads the held-out eval files from `datasets/evals/<artist_id>/`
- creates deterministic baseline predictions from the input context only
- scores those predictions against the eval rubric
- writes per-task predictions, per-task score files, and an aggregate report

If you already have model outputs in the same task file shape, score them directly:

```powershell
python score_artist_eval_predictions.py `
  --artist-id ado `
  --project-root . `
  --predictions-dir datasets/eval_runs/ado/heuristic_baseline_v1/predictions
```

Why this matters:

- it proves the eval format is executable, not just documented
- it gives a baseline to beat when a real model is connected
- it reveals which tasks are easy or hard before scaling to more artists
