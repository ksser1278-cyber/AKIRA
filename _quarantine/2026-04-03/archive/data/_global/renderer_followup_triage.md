# Renderer Follow-up Triage Guide (AKIRA ENGINE)

This guide maps failure patterns identified during smoke tests to minimal, low-cost modifications in the **Demo Renderer** layer.

## 1. Title Binding Failures

- **Symptom:** The requested title appears only once, late, or inaccurately in high-tension sections.
- **Likely Renderer Issue:** Chorus opening templates are too generic or lack title-slot priority.
- **Low-Cost Fix:** Add artist-specific chorus opening templates that explicitly anchor the title.
- **Avoid:** Completely rewriting the title selection logic.

## 2. Motif Landing Failures

- **Symptom:** `imagery_seed_list` keywords land in low-impact verses or fail to appear in the hook.
- **Likely Renderer Issue:** Motif weighting is uncalibrated for section transitions.
- **Low-Cost Fix:** Update section-specific weighting for imagery seeds in the renderer.
- **Avoid:** Defining 100+ new keywords; fix the "landing" logic first.

## 3. Surface Japanese Failures

- **Symptom:** Awkward particle attachment or broken mora grids under constraint.
- **Likely Renderer Issue:** Rewrite rules/slot insertion logic is too loose for phonetic stutters.
- **Low-Cost Fix:** Tighten the surface-level rewrite logic in the phrase shaper before adding more phrase banks.
- **Avoid:** Hardcoding every single phrase; focus on the structural "rewrite" rules.

## 4. Generic Fallback Failures

- **Symptom:** The song sounds like default pop (e.g. generic love/longing) despite artist constraints.
- **Likely Renderer Issue:** Mode-level defaults outweigh the specific `persona_seed`.
- **Low-Cost Fix:** Raise the weighting of artist-specific constraints and `leakage_guardrails` in renderer selection.
- **Avoid:** Creating a new renderer branch from scratch; tune the existing weights.

## 5. Artist Voice Collapse Failures

- **Symptom:** The persona shifts (e.g. Maretu starts acting like DECO*27 halfway through).
- **Likely Renderer Issue:** Section-by-section context memory is leaking or default tropes are creeping in.
- **Low-Cost Fix:** Reinforce the `persona_seed` and artist-specific templates in each section pass.
- **Avoid:** Adding large new narrative layers before fixing section templates.

## 6. Low-Cost Fixes First

- **Template Tuning:** Modifying chorus opening lines.
- **Weight Adjustments:** Increasing the impact of `leakage_guardrails`.
- **Constraint Clipping:** Fixing broken mora counts in the phrase shaper.

## 7. Fixes to Avoid (Early Phase)

- **Massive Data Expansion:** Do not add 50+ new phrases per artist until the structural logic (Title Binding/Motif Landing) is proven.
- **Cross-Component Refactors:** Avoid changing the Planner-Renderer interface; work within the existing dictionary mapping.

---
**Status:** implementation-ready
**Related Document:** [Smoke Test Review Sheet](demo_smoke_test_review_sheet.md)
