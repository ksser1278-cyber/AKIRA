# phase2_extended_cleanup Brief: kanaria

- workflow `extended_cleanup`
- keep track_id stable
- submit merge-friendly JSON only
- use bundled `source_records/` copies in this package as the reference input
- write output patches to this package's `incoming/` directory
- do not submit mojibake, unreadable text, or generic English summary lines
- replace placeholder/scaffold text with section-complete grounding
- remove surface-noise lines from sections and hook_lines
- set song_intent.narrative_role to exactly one supported mode
