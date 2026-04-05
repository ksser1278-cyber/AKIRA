# Archetype Consumption Guidance (AKIRA ENGINE - v1.1 Canonical)

This document defines the strict technical rules for how the AKIRA ENGINE pipeline (Planner, Renderer, Critic) consumes `artist_archetype` JSON assets. It is aligned with the conservative `engine_flags` established in Phase 12.3.

---

## 1. Safety & Policy Baseline

All Core 8 archetypes currently operate under a **Strict Security Policy**:

- **`safe_for_planner`**: **true** (Planner can ingest raw JSON for structural logic)
- **`safe_for_renderer`**: **false** (Renderer MUST NOT copy text fragments to surface)
- **`safe_for_lexical_sampling`**: **false** (No direct random sampling of phrase/imagery tokens)

---

## 2. Field-Specific Consumption Rules

### A. Planner-Safe Fields (Direct Ingestion)

The `demo_planner.py` uses these fields to establish the song's logical blueprint.

- **`core_identity`**: Establishes the persona's tone and perspective.
- **`title_patterns`**: Defines the naming logic (Bait, Noun-Chain, etc.).
- **`hook_construction`**: Sets the mora-grid and rhythmic density requirements.
- **`verse_behavior` / `bridge_final_chorus_behavior`**: Sets the structural energy flow.

### B. Renderer-Unsafe Fields (Conservative Handling)

The `demo_songwriter.py` or equivalent renderer must treat these as **indirect constraints**, not templates.

- **`common_imagery`**: **[Policy: Renderer-Unsafe]** DO NOT use these words directly. Transform them into original metaphors (e.g., if imagery is 'venom', generate 'corrosive relationship').
- **`fingerprint_pool`**: **[Policy: Sampling-Unsafe]** Use as tactical reference only. The renderer should mimic the *intent* (e.g., 'stuttering') rather than sampling the specific example phrases.
- **`safe_originality_zone`**: Use to set environmental boundaries, avoiding anchor track environments (e.g., avoid 'operating table' if it belongs to an anchor track record).

---

## 3. Safe Rollout Order (Implementation Pipeline)

The engine must expand artist coverage using this 4-step sequence:

1. **Planner Ingestion:** Planner consumes the canonical JSON to derive high-level structural constraints.
2. **Constraint Transformation:** Renderer receives "pre-approved transformed constraints" (e.g., "Use 4-mora staccato in Hook" instead of raw archetype text).
3. **Critic-Level Gating:** `demo_critic.py` cross-checks the output for `anchor leakage` or `title binding collapse`.
4. **Smoke Test Verification:** Success is verified via the `demo_smoke_test_matrix` artifact before the artist is marked as "Ready".

---

## 4. Known Anti-Patterns (Rejection Criteria)

### ❌ Pattern 1: Template-Heavy Phrasing

The generator fills structural slots with archetype keywords (e.g., [Imagery] + [Mode Structure]).

- **Effect:** Result feels mechanical and lacks artistic flow.
- **Fix:** Use archetype data as a negative constraint or structural guide.

### ❌ Pattern 2: English Token Contamination

Archetype metadata (e.g., "KING", "BUG") leaks into Japanese-only lyrical contexts.

- **Effect:** Broken aesthetic immersion.
- **Fix:** Filter for `non-kana/kanji` tokens in the `demo_critic.py`.

### ❌ Pattern 3: Anchor Leakage

Verbatim phrases from 'example-notes' or 'title_patterns' appear in the output.

- **Effect:** Immediate copyright risk and lack of originality.
- **Fix:** Prohibit direct lexical sampling when `safe_for_lexical_sampling = false`.

### ❌ Pattern 4: Renderer Fallback (Genericism)

The renderer fails to apply specific constraints and defaults to "Generic Direct Emotional Pop".

- **Effect:** All artists sound like a unified, uninteresting 'system voice'.
- **Fix:** Verify `section motif landing` in the critic layer.

### ❌ Pattern 5: Title Binding Collapse

The title generated does not match the requested artist's branding logic.

- **Effect:** Cognitive dissonance between the 'Artist Label' and the song content.
- **Fix:** Enforce strict adherence to `title_patterns` logic in the planner.

---

**Policy Status:** enforceable
**Design Reference:** `artist_coverage_audit`
