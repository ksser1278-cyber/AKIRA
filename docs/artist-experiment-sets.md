# Artist Experiment Sets

Once a single-artist package exists, split it into smaller instruction tasks so experiments are easier to run and compare.

Example:

```powershell
python build_artist_experiment_sets.py `
  --artist-id ado `
  --project-root .
```

Default output:

- `datasets/experiments/<artist_id>/mode_selector.jsonl`
- `datasets/experiments/<artist_id>/structure_planner.jsonl`
- `datasets/experiments/<artist_id>/hook_planner.jsonl`
- `datasets/experiments/<artist_id>/style_prompt_builder.jsonl`
- `datasets/experiments/<artist_id>/full_song_brief.jsonl`

Why split the tasks:

- `mode_selector`
  - tests whether the model can choose the right Ado-adjacent lane

- `structure_planner`
  - tests whether the model can map evidence into a reusable song form

- `hook_planner`
  - tests whether the model can design repetition and hook density

- `style_prompt_builder`
  - tests SUNO-style prompt conditioning quality

- `full_song_brief`
  - tests end-to-end planning quality in one shot

This is the easiest way to start with one artist first, compare task difficulty, and find which supervision style is the most effective before scaling to more artists.
