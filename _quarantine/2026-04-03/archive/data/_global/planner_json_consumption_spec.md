# Planner JSON Consumption Spec

This specification defines JSON-first archetype loading and mapping for the demo planner.

---

## 1. Engine Loading Strategy

Loading priority:

1. `<artist_id>_archetype.json`
2. `<artist_id>_archetype.md`
3. planner internal defaults

---

## 2. Field Mapping Spec

| JSON Field (Canonical) | Internal Mapper Attribute | Transformation Constraint |
| :--- | :--- | :--- |
| `core_identity` | `persona_seed` | Static grounding for plan identity. |
| `title_patterns` | `title_strategy_seed` | Map to title strategy constraints. |
| `hook_construction` | `hook_blueprint_constraints` | Map to hook blueprint constraints. |
| `verse_behavior` | `section_movement_A` | Map to verse pace and stance guidance. |
| `bridge_final_chorus_behavior` | `section_movement_B` | Map to late-section transition guidance. |
| `common_imagery` | `imagery_seed_list` | Use as imagery seed list. |
| `emotional_arc_types` | `section_arc_selection` | Map to section arc selection. |
| `leakage_risks` | `leakage_guardrails` | Map to leakage guardrails. |
| `safe_originality_zone` | `originality_boundary_hints` | Map to originality boundary hints. |

---

## 3. Validation Rules

### A. Required Fields (Strict Validation)

The planner expects these sections to be present in the JSON:

- `core_identity`
- `title_patterns`
- `hook_construction`
- `verse_behavior`
- `bridge_final_chorus_behavior`
- `common_imagery`
- `emotional_arc_types`
- `leakage_risks`
- `safe_originality_zone`

### B. Optional / Reference-Only Fields

- `fingerprint_pool`: Optional. Planner ignores by default. Direct renderer use is forbidden. Lexical sampling is forbidden.
- `notes`: Reference-only.

### C. Reference-Only Handling

- `fingerprint_pool`: Optional field. Planner ignores by default. No delivery to renderer surface. Lexical sampling forbidden.
- `notes`: Ignored.

---

## 4. Failure Handling

- **Schema Mismatch:** Partial failure. Log `SchemaWarning` and attempt key-mapping.
- **Missing Required Field:** Fallback to markdown if available; otherwise use planner internal defaults.

---

## 5. Fields to Ignore (Planner Stage)

To maintain separation of concerns, the **Planner** stage must treat these as non-operational:

- `engine_flags`
- `fingerprint_pool` (Reference-only; do not pass to downstream components).
- `notes` (Ignored).

---

**Spec Status:** implementation-ready
**Design Context:** Archetype Consumption Guidance
