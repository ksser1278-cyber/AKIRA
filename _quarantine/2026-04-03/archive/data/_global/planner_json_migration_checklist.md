# Planner JSON Migration Checklist (AKIRA ENGINE)

This checklist covers the transition of `demo_planner.py` from **Markdown-First** to **JSON-First** loading. Use this to verify your changes after implementation.

## 1. Loader Logic Changes

- [ ] Loader attempts to locate `<artist_id>_archetype.json` before `.md`.
- [ ] Path joining uses absolute system roots (no hardcoded relative links).
- [ ] `json.load()` is protected by a try-except block for `JSONDecodeError`.
- [ ] Fallback to `.md` legacy parser is triggered only if JSON is missing or corrupt.

## 2. Validation & Fallback

- [ ] **Core identity check:** If `core_identity` is null/empty in JSON, trigger fallback or use internal defaults.
- [ ] **Field parity skip:** If optional fields (e.g. `notes`) are missing, the loader continues without warning.
- [ ] **Schema consistency:** Non-schema keys are ignored and do not crash the dictionary update.

## 3. Plan Mapping Verification

- [ ] `title_patterns` -> Mapped correctly to internal `title_strategy_seed`.
- [ ] `hook_construction` -> Mapped correctly to `hook_blueprint_constraints`.
- [ ] `common_imagery` -> Mapped correctly to `imagery_seed_list`.
- [ ] `emotional_arc_types` -> Mapped correctly to `section_arc_selection`.
- [ ] `leakage_risks` -> Mapped correctly to `leakage_guardrails`.
- [ ] `safe_originality_zone` -> Mapped correctly to `originality_boundary_hints`.

## 4. Strict Reference Policy

- [ ] `fingerprint_pool` is excluded from the dict passed to the renderer stage.
- [ ] No lexical sampling logic is executed using JSON-resident phrase arrays.
- [ ] `engine_flags` remain unconsumed at the planner stage.

## 5. Failure Cases to Test

- [ ] **Missing JSON path case:** Verify fallback to `.md` when JSON is unavailable.
- [ ] **Corrupt JSON case:** Verify fallback behavior on JSON parse failure.
- [ ] **Partial JSON case:** Verify fallback to internal defaults or MD when required fields are missing.

## 6. Regression Watchpoints

- [ ] Legacy `.md` artists (e.g. Eve, Giga) still load correctly via the markdown parser.
- [ ] `mode_id` specific defaults are still applied if archetypes are missing entirely.
- [ ] Existing `deco27/pinocchiop` benchmark outputs remain stable.

---
**Status:** implementation-ready
**Reference:** [Planner JSON Consumption Spec](planner_json_consumption_spec.md)
