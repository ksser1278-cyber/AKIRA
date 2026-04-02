# SUNO Prompting Notes

This note captures the practical Suno prompting rules that currently give the best return for this project.

## Core Rules

1. Prefer a detailed natural-language style prompt over a short tag pile.
2. Keep the style prompt focused on sound, arrangement, energy, vocal tone, and arc.
3. Keep lyrical control mostly in the lyrics box, not in the style field.
4. Use `Exclude Styles` aggressively to block wrong genre drift and arrangement drift.
5. Treat one good generation as editable material. Use `Replace Section` or `Quick Replace` before rerolling the entire song.
6. Save strong voice-and-style matches as a `Persona` so later runs stay consistent.
7. Use a short `Inspire` list when you want style transfer. Three to five tightly related songs is usually better than a huge mixed pool.
8. If the instrumental is already close, try `Add Vocals` instead of regenerating everything.

## Style Prompt Rules

- Lead with genre, tempo, vocal type, and energy.
- Add arrangement and production clues next.
- Describe the emotional arc and the final-chorus payoff.
- Keep it concrete: drums, synth glow, guitar edge, close-mic verses, wide final chorus.
- Avoid stuffing full lyrical story beats or long hook text into the style prompt.

Good shape:

```text
Create a cinematic J-pop track at midtempo with an intimate Japanese lead vocal and emotional dynamic lift. Use close-mic verses, hook-forward choruses, wide final-chorus release, neon-night atmosphere, and a dramatic modern pop-rock production. Keep the verses restrained and save the clearest release for the last chorus.
```

## Lyrics Box Rules

- First pass: paste the lyrics cleanly with section headers such as `[verse_1]`, `[chorus]`, and `[bridge]`.
- Keep the lyrics mostly in one language if you want stable Japanese output.
- Only add a short context header if Suno keeps missing the language, emotional arc, or hook focus.
- Do not overload the lyrics box with long production instructions.

Useful fallback header:

```text
Japanese original lyrics. Hook phrase: <hook>. Arc: rise section by section and save the clearest release for the final chorus.
```

## Slider Starting Points

- `Style Influence`: start around `70-85%`
- `Weirdness`: start around `35-55%`
- `Prompt Influence`: keep moderate when the style prompt is already detailed
- `Prompt Boost`: try `On` first, then turn it `Off` if the output becomes too literal or stiff

## Editing Workflow

1. Start in `Custom` mode with the detailed style prompt.
2. If the result is musically close but lyrically off, keep the style and revise the lyrics input.
3. If only one section fails, use `Replace Section` or `Quick Replace`.
4. If the voice is right, save a `Persona`.
5. If the arrangement is right but the topline is weak, try `Add Vocals`.

## How AKIRA ENGINE Uses This

The current Suno bundle exporter writes:

- a detailed style prompt
- a shorter tag prompt backup
- an exclude prompt
- lyrics-box guidance with an optional context header
- creative slider guidance
- workflow tips for editing and reuse

Build bundles with:

```powershell
python build_suno_song_bundle.py `
  --scoring-manifest reports/quality/gemini_songwriter_roundtrip_v4_promptclean_test/scoring_manifest.json `
  --output-dir outputs/suno_song_bundle/ado_promptclean88 `
  --min-score 88
```

## Official Source Trail

These notes were aligned to current official Suno help-center guidance, especially the help articles surfaced by the queries below:

- `Detailed Style Instructions`: <https://support.suno.com/hc/en-us/search?query=Detailed%20Style%20Instructions>
- `Better Prompts in Lyrics`: <https://support.suno.com/hc/en-us/search?query=Better%20Prompts%20in%20Lyrics>
- `Creative Sliders`: <https://support.suno.com/hc/en-us/search?query=Creative%20Sliders>
- `Persona`: <https://support.suno.com/hc/en-us/search?query=Persona>
- `Add Vocals`: <https://support.suno.com/hc/en-us/search?query=Add%20Vocals>
- `Inspire`: <https://support.suno.com/hc/en-us/search?query=Inspire>
- `Exclude Styles`: <https://support.suno.com/hc/en-us/search?query=Exclude%20Styles>
