# Profile Derivation

## Purpose

Bridge the gap between lyric analysis evidence and the structured artist profile used by the generation pipeline.

## Flow

1. Normalize lyric files
2. Analyze tracks
3. Aggregate artist evidence
4. Derive a draft profile
5. Review and refine the draft by hand

## Command

```powershell
python derive_artist_profile.py `
  --analysis lyrics/analyzed/artists/demo.json
```

## Important Constraint

The derived profile is a draft.

It can infer:

- imagery banks
- structural defaults
- hook tendencies
- likely mode lanes
- narrative perspective
- emotional movement

It cannot reliably infer full vocal/audio truth from lyrics alone.

That is why generated profiles include review notes and conservative vocal placeholders.
