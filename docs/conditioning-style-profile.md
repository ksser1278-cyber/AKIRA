# Conditioning Style Profile

This layer turns validated `track_conditioning_record` files into an artist-level style prompt profile that the existing Suno selector can use immediately.

## Why This Exists

After the reference-track conditioning records are clean, the next question is:

`Which atoms actually repeat across the artist's strongest reference songs?`

Instead of hand-copying those signals into `style_prompt_profile.json`, this pipeline:

1. reads `data/reference_tracks/<artist_id>/*.conditioning.json`
2. infers a coarse mode for each track
3. aggregates recurring prompt atoms
4. writes a generated profile
5. writes an evidence report with track-to-mode assignments

## Output Files

For artist `ado`, the pipeline writes:

- `artists/ado/style_prompt_profile.generated.json`
- `reports/style_prompt_profiles/ado_conditioning_style_profile.md`

The loader in `src/akira_engine/style_prompt_content.py` still prefers the hand-authored `style_prompt_profile.json`.
Use the generated profile as evidence and a merge candidate, not as an automatic replacement.

## Current Scope

This aggregation is intentionally conservative.

- `global_atoms` are aggregated from all validated reference tracks
- `mode_atoms` are aggregated from inferred mode groups
- `axis_atoms` are copied from the existing base profile for now

That means the generated profile is immediately usable without pretending we have reliable axis labels inside every conditioning record yet.

## Run

```powershell
python scripts/pipeline/build_conditioning_style_profile.py `
  --artist-id ado `
  --project-root .
```

## Notes

- The generated profile is meant to be machine-usable first.
- It preserves the existing mode ids so downstream prompt selection does not break.
- `ready_for_audio_claims` on the source conditioning records should still be treated separately from prompt usability.
