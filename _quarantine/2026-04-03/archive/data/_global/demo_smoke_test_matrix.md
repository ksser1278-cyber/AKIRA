# Demo Smoke Test Matrix

This matrix defines the priority test cases for the AKIRA ENGINE demo pipeline, ensuring that the **Canonical Artist DNA** is correctly synthesized within different **Mode Support** contexts using the local `demo_songwriter` environment.

## 1. Primary Smoke Test Priorities

| Artist ID | Mode ID | Purpose | Success Marker | Priority |
| :--- | :--- | :--- | :--- | :---: |
| **DECO*27** | direct_emotional_pop | **Baseline** | Somatic urgency + bratty interjection density. | **Highest** |
| **PinocchioP** | ironic_meta | **Baseline** | Informational load + sarcastic title binding. | **Highest** |
| **MARETU** | dark_cute_breakdown | High Friction | Clinical social judgment + Keigo-dissonance. | **High** |
| **Kanaria** | ironic_meta | Data Verification | Status-title drop ignition + minimalist grit. | **High** |
| **Kairiki Bear** | direct_emotional_pop | Density Test | Stuttering pre-hook loops + toxic monologue. | **High** |
| **Iyowa** | ironic_meta | Distortion Test | Organic-mechanical noun fusion + verb-loops. | **High** |
| **Syudou** | direct_emotional_pop | Irony Test | Diagnostic interjections + bitter resentment. | **High** |
| **Neru** | ironic_meta | Tone Test | Anti-authoritarian surgical rock commands. | **High** |

## 2. Technical Metrics (Pass/Fail Signals)

### Pass Metrics (Success)

- **Title Binding Stable:** The generated title correlates to the selected pattern without directly cloning anchors.
- **Section Motif Landing:** Artist-specific keywords (e.g., medical, carnival, industrial) appear in the correct sections.
- **Surface Japanese Quality:** High ratio of kanji/kana usage consistent with the artist's vocabulary profile.
- **Mode Fit Stability:** Transition from "Direct" to "Breakdown" maintains the established artist persona.

### Failure Metrics (Rejection)

- **Renderer Fallback:** The output defaults to generic pop tropes (e.g., "Always together", "Shining future").
- **Artist Voice Collapse:** The persona is lost in a broad genre template (e.g., generic generic rock for Neru).
- **Template-Heavy Phrasing:** Repetitive structural fill-ins that feel mechanical.
- **Anchor Leakage:** Verbatim use of forbidden phrases from the `archetype.md` example notes.

---

## 3. Execution Guidance

1. **Stage 1 (Baseline):** Verify DECO*27 and PinocchioP. If these fail, the core prompt injection logic is broken.
2. **Stage 2 (Friction):** Run MARETU and Syudou. These tests reveal the limits of the engine's ability to handle linguistic dissonance and irony.
3. **Stage 3 (Density):** Run Kairiki Bear and PinocchioP. Verify that informational density does not break the `surface japanese quality`.

**Report Status:** active
**Target Version:** 1.0 (Canonical)
