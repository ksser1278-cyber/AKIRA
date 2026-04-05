# Generation Safety Phase1 Internal Normalization

- status: `complete`
- tracks: `0`
- artists: `0`

## Goal

- take validated lyric-grounding source bundles and normalize them into phase1 grounding patches
- preserve trusted lyric text while expanding from compressed `verse` / `chorus` bundle sections into the current 5-section conditioning schema

## Required Internal Work

- map exact lyric text from source bundles into current `verse`, `prechorus`, `chorus`, `bridge`, and `final chorus` slots conservatively
- replace scaffold hook lines with grounded hook lines from the source bundle
- remove scaffold language from `source_provenance.notes`, `song_intent.emotional_thesis`, and copyright notes
- keep provenance and narrative role unchanged unless the validated bundle proves a contradiction
