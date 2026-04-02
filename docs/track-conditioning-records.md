# Track Conditioning Records

This schema is the dataset-first version of a human deep-analysis sheet.

The goal is not to create a pretty writeup. The goal is to create records that are:

- consistent across many songs
- comparable across artists
- directly reusable for style prompting
- safe about certainty levels

## Why This Is Better Than Free-Form Analysis

A manual sheet like:

- instrumentation
- harmony / melody
- dynamics
- pattern
- vocabulary
- rhyme
- rhythm

is useful for humans, but poor as a scalable dataset because each section is still mostly prose.

The `track_conditioning_record` splits that prose into reusable fields.

## Japanese-Lyric Layer

The schema now also carries a dedicated Japanese-lyric constraint layer.

This matters because J-pop conditioning often depends on constraints that do not fit neatly into generic pop-analysis prose:

- `A-melo / B-melo / Sabi` role clarity
- mora-ish line density
- spoken-speed compression
- title drop timing
- hook copy-force

New per-section fields:

- `jp_section_role`
- `mora_density`
- `spoken_speed_bias`
- `title_drop_role`
- `phrase_energy_role`

New top-level block:

- `japanese_lyric_profile`

The schema now also carries a generation-use safety block:

- `generation_safety`

That block is intended to carry reusable Japanese-writing constraints such as:

- `workflow_bias`
- `hook_copy_force`
- `title_ignition_style`
- `modern_compression_bias`
- `phrase_source_types`
- `accent_risk_notes`
- `critic_focus`

## Core Design Rule

Every claim should land in one of three buckets:

- `confirmed`
- `cross_checked` or `estimated`
- `inferred`

That prevents the dataset from mixing hard facts with interpretation.

This still is not enough by itself. A record can be schema-valid and still weak.

See:

- `docs/conditioning-reliability-framework.md`

That document defines how records should be graded as `gold`, `usable`, or `weak` before they are trusted for benchmark or critic work.

Current trust rule:

- `gold` requires `lyric_ground_truth.full_text_status = full`
- `partial` lyric grounding is acceptable for `usable`
- `excluded` lyric grounding should not be used for benchmark truth

Current generation-safety rule:

- `gold` does not automatically mean `generation_safe`
- `generation_safe` and `benchmark_safe` are separate runtime decisions
- `generation_safety` should be added as an optional block first, then enforced by planner/runtime later

## Field Map From The Original Analysis Style

Original heading -> structured field

- `제목 / 보컬 / 작사 / 작곡 / 편곡 / 발매일` -> `track_identity`
- `곡 의도 요약` -> `song_intent`
- `가사 전문` -> `lyric_ground_truth.sections`
- `악기/편곡` -> `section_analysis[].arrangement_role`
- `화성/멜로디` -> `section_analysis[].harmony_melody_role`
- `다이나믹스` -> `section_analysis[].dynamics_role`
- `패턴` -> `section_analysis[].rhetorical_pattern`
- `어휘` -> `section_analysis[].vocabulary_focus`
- `라임` -> `section_analysis[].rhyme_features`
- `리듬` -> `section_analysis[].rhythm_features`
- `Suno용 스타일 프롬프트 압축` -> `prompt_conditioning`

## Important Separation

Do not store these as the same thing:

- lyric-grounded observation
- reported metadata
- proxy sound inference

Example:

- `lyrics say "病名", "カルテ", "治療法"` -> lyric-grounded
- `152 BPM from SongBPM and SongData.io` -> reported / cross-checked
- `guitar-led, restrained intro, expanded final chorus` -> proxy inference

The Japanese-lyric layer sits beside those buckets. It is not a hard audio-fact layer, but it is also not just free-form commentary. It is a reusable songwriting-constraint layer.

The `generation_safety` block sits beside those buckets as an engine-use gate. It does not replace provenance or quality grading. It records whether a track is safe to use for:

- planner input
- renderer input
- lexical sampling
- benchmark evaluation

## Recommended Use

```text
lyrics + metadata + official copy + third-party cross-check
-> track_conditioning_record
-> artist-level style atoms
-> SUNO prompt builder
```

## Outputs To Expect Later

This schema is meant to back:

- per-track conditioning JSON
- artist-level style profiles
- retrieval for prompt generation
- evaluation sets for generated songs
- generation-safe planner inputs
- runtime-safe renderer assets derived from reviewed records

## Generation Safety Block

The minimum `generation_safety` block should include:

- `schema_version`
- `verdict`
- `score`
- `score_breakdown`
- `allowed_layers`
- `blockers`

Recommended `verdict` values:

- `invalid`
- `audit_only`
- `planner_safe`
- `generation_safe`
- `benchmark_safe`

Recommended minimum `score_breakdown`:

- `provenance_trust`
- `grounding_completeness`
- `surface_safety`
- `renderer_readiness`

Recommended `allowed_layers`:

- `planner`
- `renderer`
- `lexical_sampling`
- `benchmark`

Recommended blocker codes:

- `missing_provenance`
- `partial_grounding`
- `surface_noise_risk`
- `renderer_policy_block`
- `lexical_sampling_block`
- `mode_fit_unverified`
- `schema_drift_detected`
- `anchor_leakage_risk`

Rollout rule:

1. add the block as optional
2. store values without blocking runtime
3. report presence and verdicts
4. enforce planner/runtime gates only after pilot relabeling

## Files

- schema: `schemas/track_conditioning_record.schema.json`
- manifest schema: `schemas/track_conditioning_manifest.schema.json`
- template: `data/reference_tracks/_template/track_conditioning_record.template.json`
