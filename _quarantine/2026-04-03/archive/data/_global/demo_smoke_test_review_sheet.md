# Smoke Test Review Sheet (AKIRA ENGINE)

Use this sheet to evaluate the results of the 6 core smoke tests after the JSON-first migration.

| Artist ID | Mode ID | Mandatory Inspection Points | Pass Questions | Fail Signals |
| :--- | :--- | :--- | :--- | :--- |
| **Kanaria** | ironic_meta | `selected_lyric`, `run_manifest` | Does the title bind cleanly in the hook? | Hook opens with generic pop tropes. |
| **Maretu** | dark_cute_breakdown | `selected_lyric`, `demo_run_report` | Is the keigo-to-violence shift perceptible? | Repetition handling breaks surface grammar. |
| **Kairiki Bear** | direct_emotional_pop | `selected_lyric`, `critic_results` | Does stutter logic maintain mora flow? | Stutter becomes nonsensical phonetics. |
| **Iyowa** | ironic_meta | `selected_lyric`, `run_manifest` | Does imagery keep mundane grounding? | Surrealism floats into abstract dreaminess. |
| **Syudou** | direct_emotional_pop | `selected_lyric`, `demo_run_report` | Are diagnostic interjections cynical? | Tone collapses into generic shouting. |
| **Neru** | ironic_meta | `selected_lyric`, `critic_results` | Is industrial specificity maintained? | Surgical motifs lost to broad rock tropes. |

## 🔧 Triage Logic (Renderer Follow-up)

- **If Title Binding Fails:**
  - Likely: Artist chorus templates missing or generic.
  - Follow-up: Check renderer triage document.
- **If Surface Japanese Fails:**
  - Likely: Slot insertion rules too loose for repetitive or constrained phrasing.
  - Follow-up: Check renderer triage document.
- **If Generic Fallback Occurs:**
  - Likely: Artist-specific shaping is too weak in key sections.
  - Follow-up: Check renderer triage document.

---
**Status:** Verification Ready
**Reference:** [Renderer Expansion Priority](renderer_expansion_priority.md)
