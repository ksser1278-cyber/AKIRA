# Reference Track Dossiers

Automatic lyric analysis is useful, but it cannot fully capture why a song works.

For higher-quality conditioning, the project also needs a manual reference layer that stores:

- what the song is trying to do
- how the arrangement supports that goal
- what emotional contrast makes it memorable
- how each section changes the dramatic state

## Why This Exists

The auto intent layer can infer:

- tie-in role
- likely purpose bucket
- structure shape
- imagery and hook density

But it cannot reliably infer:

- the exact contrast strategy between lyrics and harmony
- why the chorus feels like release instead of just repetition
- how instrumentation changes section meaning
- what should be imitated in a SUNO style prompt

## Intended Flow

```text
raw -> normalized -> curated -> auto intent cards -> manual reference dossiers -> prompt conditioning
```

## Dossier Contents

A good dossier should describe:

- track identity and production facts
- one-sentence core purpose
- emotional engine and contrast device
- section-by-section intent
- distilled SUNO conditioning hints
- what must be preserved and what must be avoided

## Example

- `data/reference_tracks/pinocchiop/bokunankaiinakutemo.intent.json`

This example does not store verbatim lyrics. It stores reusable intent evidence instead.
