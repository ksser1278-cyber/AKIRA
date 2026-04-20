# Corpus-Driven Proposition Engine

## Definition

AKIRA lyric generation is defined as a `Corpus-Driven Proposition Engine`.

The engine does not start from motif extraction or fixed section templates. It starts from:

1. corpus intelligence
2. composition brief
3. proposition selection
4. form selection
5. section behavior planning
6. realization
7. evaluation with novelty-aware selection

The planning center is `proposition / form / line behavior`, not `motif / template / section-card-first`.

## Layer Model

### 1. Corpus Intelligence Layer

Inputs:
- conditioning records
- lyric behavior priors
- form family catalog

Outputs:
- `artist_style_prior`
- `form_family_prior`
- `proposition_signal_bank`
- `line_behavior_bank`
- `lexical_field_bank`

Rules:
- raw corpus does not go directly to renderer
- corpus is converted into decision signals only

### 2. Composition Brief Layer

Primary artifact: `composition_brief`

Required fields:
- `song_purpose`
- `listener_position`
- `chorus_proposition`
- `singability_profile`
- `energy_curve`
- `artist_grammar_bias`
- `mode_bias`

Rule:
- planning starts from brief, not from mode

### 3. Proposition Engine

Primary artifact: `proposition_archetype_set`

Each proposition contains:
- `proposition_id`
- `core_phrase`
- `escalation_phrase`
- `release_phrase`
- `allowed_lexical_families`
- `forbidden_fragments`
- `hook_density_target`
- `title_return_policy`
- `novelty_signature`

Rules:
- hook is determined before rendering
- non-chorus sections must not directly reuse hook fragments
- same mode may yield different propositions

### 4. Form Engine

Primary artifact: `form_plan`

Fields:
- `form_family_id`
- `form_family_reason`
- `section_order`
- `section_count`
- `line_target_profile`
- `repetition_budget_profile`
- `pressure_transition_profile`

Rules:
- `mode 1 = form 1` is forbidden
- mode provides shortlist and bias only
- final form is chosen from proposition + artist prior + form prior

Current rollout:
- `dark_cute_breakdown`
- allowed families: `compressed_hook`, `hybrid_release`

### 5. Section Behavior Engine

Primary artifact: `section_behavior_plan`

Each section defines:
- `section`
- `section_role`
- `pressure_stage`
- `semantic_carry`
- `hook_dependency`
- `line_target_range`
- `cadence_target`
- `repetition_budget`
- `closure_strength_target`
- `allowed_lexical_families`
- `blocked_hook_fragments`

Rules:
- `verse_2` escalates pressure, not topic
- `pre_chorus_2` accelerates pressure, not meaning
- `chorus_final` is the only irreversible release zone

### 6. Realization Engine

Renderer responsibility is limited to execution.

Renderer reads:
- proposition
- form
- section behavior
- lexical constraints
- artist grammar bias

Renderer must not:
- invent structure
- create proposition
- interpret raw corpus directly
- reintroduce mode-locked templates

### 7. Evaluation and Selection Engine

Selection is based on:
- `legacy_total`
- `musical_total`
- `novelty_score`
- `blended_total`

Required outputs:
- `winner_candidate_id`
- `winner_reason`
- `legacy_total`
- `musical_total`
- `novelty_score`
- `blended_total`
- `proposition_distance`
- `form_distance`
- `surface_overlap_penalty`

Rule:
- repeated safe winners are a failure mode
- novelty is used to prevent repeated proposition/surface/form convergence

## Public Artifacts

### Engine Input
- `artist_id`
- `mode_id`
- `intent`
- `title_seed`
- `candidate_count`

### Runtime Artifacts
- `composition_brief`
- `proposition_archetype_set`
- `selected_proposition`
- `form_plan`
- `section_behavior_plan`
- `candidate_packages`
- `evaluation_manifest`

### Output Package
- `corpus_intelligence.json`
- `composition_brief.json`
- `proposition_archetype_set.json`
- `runtime_plan.json`
- `candidate_packages.json`
- `evaluation_manifest.json`
- `selected_lyric.md`
- `run_manifest.json`

## Removed Primary Concepts

The following are no longer primary planning concepts:
- fixed section blueprints tied directly to mode
- motif-first song generation
- old section cards as the main planning artifact
- renderer-led structural differentiation

## Acceptance Standard

The engine is working only if:
- different artists can produce different propositions under the same mode
- form family is selected from proposition and priors, not fixed by mode
- section behavior explains pressure movement, not generic structure labels
- repeated winner convergence is penalized through novelty
- corpus influence is traceable through proposition, form, and line behavior
