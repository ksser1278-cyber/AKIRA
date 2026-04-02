# Conditioning Reliability Framework

## Purpose

The project should not trust a conditioning record just because the schema validates.

Schema validity only means:

- the file is structurally well-formed
- required keys exist

It does **not** mean:

- the analysis is correct
- the evidence is strong
- the record should be used for benchmarking

This framework defines how to measure that.

## Reliability Principles

### 1. Separate format quality from content quality

A record can be schema-valid and still be weak.

Examples:

- too many inferred claims
- sparse hook coverage
- weak provenance
- section analysis that is technically present but low-information

### 2. Do not over-reward completeness theater

Filling every field with generic prose lowers trust.

Weak examples:

- `core_theme = loneliness`
- `energy_profile = strong`
- `production_palette = emotional`

These satisfy structure but do not carry reusable signal.

### 3. Trust should come from provenance and repeatability

A strong conditioning record should make it possible for another operator to answer:

- where this fact came from
- how certain it is
- whether the same result can be reproduced

## Required Reliability Buckets

Every meaningful claim should be treated as one of:

- `confirmed`
- `cross_checked`
- `estimated`
- `inferred`
- `unknown`

Interpretation-heavy fields should also carry confidence pressure through:

- `high`
- `medium`
- `low`

## Audit Grades

### `gold`

Use for:

- benchmark input
- critic tuning
- planner tuning
- cross-artist comparisons

Requirements:

- strong provenance
- full lyric grounding
- multiple hook lines
- section map present
- prompt conditioning dense enough for reuse
- few or no missing fields
- high-trust evidence ratio acceptable
- `lyric_ground_truth.full_text_status = full`

### `usable`

Use for:

- planner input
- style retrieval
- mode prototyping

Do not use as the main benchmark truth set if a gold alternative exists.

Typical issues:

- partial lyric coverage
- sparse section notes
- too many estimated fields
- manual review still needed

Rule:

- `partial` lyric grounding is allowed here
- `gold` is not allowed unless lyric grounding is `full`

### `weak`

Use for:

- reference only
- not benchmarking
- not critic tuning

Typical causes:

- excluded lyric text
- weak provenance
- missing section analysis
- hook lines absent
- inferred claims dominate the record

## Audit Dimensions

Each record should be measured on at least these dimensions.

### Provenance strength

Checks:

- `lyric_sources` exists
- `metadata_sources` exists
- key fields cite official or cross-checked sources

### Lyric grounding

Checks:

- `full_text_status`
- number of grounded lyric sections
- hook line count
- repetition pattern capture

Minimum trust rule:

- `full` can qualify for `gold`
- `partial` can qualify for `usable`
- `excluded` or unknown should not be benchmark truth

### Structural resolution

Checks:

- section count
- section role coverage
- `jp_section_role` presence

### Intent resolution

Checks:

- `core_theme`
- `contrast_device`
- `dramatic_arc`
- `narrative_role`
- `title_function`
- `key_motifs`

### Prompt usefulness

Checks:

- density of `genre_anchors`
- density of `tempo_feels`
- density of `vocal_tones`
- density of `production_palette`
- density of `imagery_anchors`
- usable exclude list

### Risk flags

Checks:

- `missing_fields`
- `manual_review_required_for`
- overuse of `estimated` and `inferred`

## Operational Rule

Do not tune the engine against all conditioning files equally.

Use:

- `gold` for benchmark truth
- `usable` for planner coverage
- `weak` for reference only

If this rule is ignored, the engine will learn from noisy or over-asserted records and drift toward generic outputs.

## Implemented Audit Tool

Run:

```powershell
python scripts/pipeline/audit_conditioning_records.py `
  --artist-id pinocchiop `
  --project-root .
```

Outputs:

- `reports/quality/conditioning/<artist>_conditioning_audit.json`
- `reports/quality/conditioning/<artist>_conditioning_audit.md`

## Immediate Usage Recommendation

For now, re-audit at least:

- `pinocchiop`
- `deco27`

Then:

1. use only `gold` records as benchmark truth
2. keep `usable` records available for planner coverage
3. exclude `weak` records from tuning decisions
