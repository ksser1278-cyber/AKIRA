# Scripts Stage 2 Quarantine

Moved on `2026-04-03`.

## Purpose

Reduce the active `scripts/` surface without deleting historical tooling.

## Quarantined Items

- `scripts/oneoff/`
- `scripts/autonomous_cycle_demo.py`
- `scripts/mastery_demo_run.py`
- `scripts/smoke_week3_integration.py`
- `scripts/smoke_week4_integration.py`
- `scripts/smoke_week7_integration.py`
- `scripts/test_day1_originality_admission.py`
- `scripts/test_day2_diversity_constraints.py`
- `scripts/test_failure_modes.py`
- `scripts/test_glitch_count.py`
- `scripts/test_sprint_regression.py`
- `scripts/test_week1_novelty.py`
- `scripts/test_week2_clusters.py`
- `scripts/test_week3_motifs.py`
- `scripts/test_week4_hooks.py`
- `scripts/test_week5_planner.py`
- `scripts/test_week6_grounding.py`
- `scripts/test_week7_narrative.py`
- `scripts/test_week8_canon.py`
- `scripts/test_week9_routing.py`
- `scripts/test_week10_constraints.py`
- `scripts/test_week11_master_prompt.py`
- `scripts/test_week12_final_audit.py`
- `scripts/verify_phase_5.py`

## Rationale

These files were not part of the current CLI surface and represented ad-hoc or historical execution paths that make the rebuild workspace harder to reason about.

They were moved, not deleted.
