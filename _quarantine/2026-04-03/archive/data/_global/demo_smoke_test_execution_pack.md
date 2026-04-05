# Demo Smoke Test Execution Pack

This document defines the **Execution Gates** for verifying the 6 core artists currently in `Partial/High-Friction` status. These tests should be run AFTER the `demo_planner.py` has been updated to use the JSON-first loading logic.

---

## 1. Execution Matrix

| Artist ID | Pass Gate (Mandatory Inspection) | Failure Signal |
| :--- | :--- | :--- |
| **Kanaria** | Title binding remains stable in hook opening. | Lacks artist-specific phrase shaping. |
| **Maretu** | Repetition handling does not break phrase surface. | Defaults to generic dark phrasing. |
| **Kairiki Bear** | Rhythmic stutter logic maintains mora grid. | Repetition handling drift detected. |
| **Iyowa** | Imagery remains specific and mode-consistent. | Surreal-mundane logic collapse. |
| **Syudou** | Artist-specific phrasing does not collapse into generic. | Tone defaults to aggressive shouting. |
| **Neru** | Surface Japanese remains stable under constraints. | Industrial-surgical specificity lost. |

---

## 2. Failure Signals (Operational Watchlist)

### 🔴 Signal A: Generic Fallback

- **Detector:** The renderer ignores JSON structural constraints (e.g., mora count) and falls back to generic pop-ballad timing.
- **Risk:** High for **Kanaria** (artist-specific title/hook branch exists but phrase bank is limited).

### 🔴 Signal B: Voice Collapse

- **Detector:** The "Artist Voice" is overridden by generic persona instructions in the prompt.
- **Risk:** High for **Maretu** (no explicit polite-cruelty phrase shaping) and **Neru** (industrial-surgical rebellion bank not explicit).

### 🔴 Signal C: Jitter Error

- **Detector:** Stuttering rules in `hook_construction` result in nonsensical phonetics or broken mora grids.
- **Risk:** High for **Kairiki Bear** (no verified recursive stutter handling branch).

---

## 3. Review Focus (Manual Check)

When reviewing the generated `selected_lyric.md`, focus on:

1. **Title Binding:** Does the title adhere to the requested branding logic?
2. **Motif Landing:** Placement of imagery nouns in Hook/Bridge.
3. **Surface Quality:** Japanese grammar and phrase stability.
4. **Artist Voice Stability:** Persona consistency across sections.
5. **Renderer Fallback Risk:** Detecting generic pop-tropes vs. artist-specific behavior.

---

**Execution Pack Status:** active
**Implementation Spec:** Planner JSON Consumption Spec
