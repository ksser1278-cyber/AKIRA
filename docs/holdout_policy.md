# Holdout Policy

## Purpose

Prevent intelligence modules from being tested on the same data they were built from.

## Directory Structure

```text
data/eval/
  holdout_external/   # Tracks excluded from intelligence building
  holdout_internal/   # Generated tracks for self-evaluation
  regression_prompts/ # Fixed prompt set for regression testing
```

## Split Method

**Stratified Split** — NOT random.

Stratification dimensions:

- Artist distribution
- Style cluster membership
- Composite score grade (elite/standard)

## Rules

1. Holdout ratio: **20%** of total corpus
2. Intelligence builders (motif mining, clustering, hook grammar) must NEVER read from `data/eval/`
3. Evaluation scripts must ONLY read from `data/eval/`
4. Same track variants (remixes, covers) must stay in the same split
5. Minimum 1 track per stratum in holdout

## Rebuild Protocol

When the corpus changes significantly (>10% new tracks):

1. Re-run `scripts/research/build_holdout_split.py`
2. Verify stratification with distribution report
3. Re-run intelligence builders on training set only
