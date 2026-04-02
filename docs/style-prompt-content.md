# Style Prompt Content

This layer exists to answer a practical question:

`What should go into the Suno style prompt for this artist and this song?`

The goal is not prettier writing. The goal is better selection.

## Principle

Style prompts work best when they carry musical information, not lyric-story overload.

AKIRA ENGINE therefore separates:

- `style prompt content`
  - genre
  - tempo feel
  - groove
  - vocal tone
  - production palette
  - arrangement moves
  - energy arc
  - exclude terms
- `lyrics box control`
  - title image
  - hook phrase
  - section structure
  - language guardrails
  - lyric imagery

## File Layout

Each artist can now define a dedicated content profile:

```text
artists/<artist_id>/style_prompt_profile.json
```

This is separate from `profile.json` so prompt-content tuning can move faster than the broader artist profile.

## Content Categories

The schema uses three layers:

1. `global_atoms`
Shared musical DNA for the artist.

2. `axis_atoms`
Theme-axis-specific color that can be injected when a plan contains axes such as `night`, `city`, `motion`, or `defiance`.

3. `mode_atoms`
Mode-specific musical choices that map to planning modes such as `intimate_confessional` or `anthemic_cinematic`.

## Selection Logic

When building a Suno bundle, the selector:

1. loads `artists/<artist_id>/style_prompt_profile.json`
2. looks up the current `primary_mode`
3. adds any matching `axis_atoms` from the plan's theme axes
4. derives a compact content card
5. uses that card to build:
   - detailed style prompt
   - tag prompt backup
   - exclude prompt

## Why This Matters

Without this layer, the prompt generator tends to guess from theme axes alone.
With this layer, the system can say:

- which two genre anchors to keep
- what groove feel should dominate
- which vocal behaviors matter most
- which production colors should appear
- what must be excluded

That makes prompt quality more intentional and much easier to tune artist by artist.

## Current Example

See:

- `artists/ado/style_prompt_profile.json`
- `schemas/style_prompt_content.schema.json`

And inspect generated bundle output at:

- `outputs/suno_song_bundle/ado_promptclean88/json/*.json`
- `outputs/suno_song_bundle/ado_promptclean88/markdown/*.md`

The exported package now contains a `style_content_card` section so the selected content is visible before you paste anything into Suno.

## Mode Probe Validation

When your scored song bundle does not yet cover every mode, you can still validate the content layer directly:

```powershell
python build_style_prompt_mode_probes.py `
  --profile artists/ado/style_prompt_profile.json `
  --output-dir outputs/style_prompt_probes/ado
```

This writes one JSON and one markdown file per mode so you can inspect:

- whether the right atoms were selected
- whether the detailed prompt sounds musically distinct
- whether the exclude terms and arc feel mode-appropriate
