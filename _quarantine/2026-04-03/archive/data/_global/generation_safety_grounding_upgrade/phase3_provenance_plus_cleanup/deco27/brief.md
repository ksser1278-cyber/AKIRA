# phase3_provenance_plus_cleanup Brief: deco27

- workflow `provenance_plus_cleanup`
- keep track_id stable
- submit merge-friendly JSON only
- use bundled `source_records/` copies in this package as the reference input
- write output patches to this package's `incoming/` directory
- do not submit mojibake, unreadable text, or generic English summary lines
- do not replace placeholders with inferred paraphrases; use grounded Japanese text copied or tightly aligned from bundled `source_records/`
- do not add English cleanup commentary to notes, thesis, or copyright fields
- replace placeholder/scaffold text with section-complete grounding
- remove surface-noise lines from sections and hook_lines
- add trusted lyric_sources and metadata_sources
- set song_intent.narrative_role to exactly one supported mode
