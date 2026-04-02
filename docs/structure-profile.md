# Structure Profiles

`artists/<artist_id>/structure_profile.json` lets the planner choose a mode-specific song shape before it writes the prompt package.

This exists because the old Songwriter V2 planner leaned too heavily on inferred form heuristics and generic section defaults. That made many outputs collapse into a similar J-pop arc even when the style prompt and conditioning record were asking for different motion.

Each mode structure can define:

- `section_order`
- `line_targets`
- `form_tags`
- `goal_overrides`
- `delivery_overrides`

Current first-use target:

- `artists/ado/structure_profile.json`

Planner behavior:

1. If a structure profile exists for the artist and current mode, use it.
2. If no structure profile exists, fall back to the inferred-form planner.
3. Section goals from the record still win when present, but the structure profile can replace generic defaults.

The immediate goal is not to make lyrics perfect by itself. The goal is to stop the planner from flattening different modes into the same structure before generation even begins.
