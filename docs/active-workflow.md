# Active Workflow

This document is the current operating contract for AKIRA ENGINE.

The main failure mode is no longer lack of data. The main failure mode is letting intake, experiments, reports, generated lyrics, and feedback mutate independently without one active contract.

## Source Of Truth

- Active config: `config/active_workflow.json`
- Validation command: `python akira.py workflow validate`
- State refresh command: `python akira.py report sync-engine-surface`
- Current state report: `reports/planning/engine_state.md`
- Current health report: `reports/health/engine_health.md`

If these disagree, trust `config/active_workflow.json` first, then update the stale document or report.

## Folder Contract

| Path | Role | Rule |
| --- | --- | --- |
| `config/` | active workflow and local templates | Keep the current workflow contract here. Do not put live secrets in tracked config. |
| `src/akira_engine/` | production logic | New user-facing behavior must land here before script shims. |
| `scripts/` | compatibility and batch utilities | Do not make this the primary user surface. |
| `data/` | small stable registries | Keep only reusable state, anchors, and technique libraries. |
| `datasets/_global/` | large acquisition lanes | Bulk metadata and grounding acquisition live here. |
| `datasets/training/` | processed training and generation workspaces | Versioned workspaces are allowed, but the active one must be named by a manifest or config. |
| `reports/planning/` | decisions and validation reports | Store state, validation, backlogs, and promotion decisions here. |
| `outputs/` | demo and experiment outputs | Every useful output must keep its plan, candidates, evaluation, and selected lyric together. |
| `_quarantine/` | inactive legacy or temporary material | Move old scrapes, one-offs, and abandoned surfaces here instead of deleting them. |

## Active Quality Loop

1. Refresh state.
   - Run `python akira.py report sync-engine-surface`.
   - Check `reports/planning/engine_state.md`.
   - Stop if stale or conflicting state appears.

2. Validate workflow reachability.
   - Run `python akira.py workflow validate`.
   - Errors block work. Warnings are allowed but must become backlog items.

3. Select source records.
   - Prefer grounded lyric-technique records with prompt-ready generation profiles.
   - Do not use raw corpus material directly in the renderer.

4. Generate a song package.
   - Run `python akira.py songwriter demo --artist-id <artist> --mode-id <mode>`.
   - Keep `composition_brief.json`, `proposition_archetype_set.json`, `runtime_plan.json`, `candidate_packages.json`, `evaluation_manifest.json`, and `selected_lyric.md` together.

5. Review with concrete feedback.
   - Mark weak lines, strong lines, missing payoff, weak mouth-feel, stale topic, and section-flow breaks.
   - Do not write generic feedback like "make it better".

6. Convert feedback into engine work.
   - Topic sameness maps to proposition and lexical-family expansion.
   - Similar song forms map to form-family expansion.
   - Pop-like smoothness maps to renderer cadence and section-contrast rules.
   - Weak hook feel maps to hook proposition, title-return, rhyme, and line-attack rules.

7. Regression check.
   - Run `python akira.py workflow validate`.
   - Run `python akira.py test`.
   - Compare new outputs against recent winner history and baseline health reports.

## Current Known Gaps

- The active proposition engine still has one wired mode profile: `dark_cute_breakdown`.
- Candidate generation is capped at four candidates.
- Active form diversity is only `compressed_hook` and `hybrid_release`.
- Active proposition diversity is four handcrafted archetypes.
- Current state has strong corpus scale, but the prompt-ready quality lane is still much smaller than the raw corpus.
- Recent winner history must be watched for repeated proposition/core/form signatures; repetition here is a direct signal that the engine is converging before it is actually improving.

These are not documentation issues. They explain why generated songs can still converge into similar topics and shapes even when the corpus is large.

## Promotion Rule

An engine change is not promoted because one demo sounds better.

Promote only when all are true:

1. Workflow validation has no errors.
2. The selected lyric package includes plan, candidates, scores, and selected lyric.
3. The new output fixes a named failure without reintroducing a baseline regression.
4. Human feedback is specific enough to become data, a rule, or a test.
