# Lyrics Analysis

## Goal

Turn normalized lyric documents into artist-level style signals that are specific enough to support:

- structured artist profiles
- lyric blueprint datasets
- prompt generation
- future lyric drafting and evaluation

The analysis stage should not answer only "what words appear often."

It should answer:

- how the artist structures songs
- how emotional intensity moves across sections
- what imagery clusters recur
- what kinds of hooks repeat
- what contrasts define the artist voice

## Core Principle

Lyrics should be analyzed at three levels at the same time:

1. track level
2. section level
3. artist aggregate level

If we skip any one of these, the output becomes too shallow.

Examples:

- only track-level analysis misses artist-wide recurrence
- only artist-level analysis misses section function
- only section-level analysis misses whole-song progression

## Recommended Analysis Layers

### 1. Structural Analysis

Question:

How does the song move?

What to measure:

- section order
- section count
- presence or absence of intro, pre-chorus, bridge, outro
- chorus repetition count
- average line count per section
- whether the chorus is shorter, denser, or more repetitive than verses

Why it matters:

This becomes the basis for section blueprints and mode defaults.

Output examples:

- common section pattern: `intro -> verse -> pre_chorus -> chorus -> verse -> chorus -> bridge -> final_chorus`
- chorus density ratio versus verse
- likelihood of a bridge before the final chorus

### 2. Repetition and Hook Analysis

Question:

Where does memorability come from?

What to measure:

- repeated lines
- repeated fragments within lines
- short hook phrases
- opening-word repetition
- chorus-internal repetition
- callback phrases that reappear later in the song

Why it matters:

A lot of artist identity shows up in how hooks repeat, not just in vocabulary.

Output examples:

- repeated phrase candidates
- hook length distribution
- chorus repetition score
- call-and-response patterns

### 3. Lexical Analysis

Question:

What kinds of words does the artist prefer?

What to measure:

- token frequency
- distinctive words versus the artist's own corpus baseline
- pronoun usage
- abstract versus concrete noun ratio
- verb intensity
- adjective polarity
- English word insertion frequency

Why it matters:

This helps separate artists who sound visually concrete from artists who sound emotionally abstract.

Important note:

Frequency alone is weak. We should care more about distinctive and repeated-in-context language than raw counts.

### 4. Imagery and Semantic Field Analysis

Question:

What image worlds recur?

What to measure:

- city / night / light / body / weather / violence / fracture / motion imagery
- image co-occurrence
- dominant noun clusters
- symbolic contrast pairs

Why it matters:

This is often more important than literal topic labels.

For example, an artist may not always sing about "rebellion," but may repeatedly use image fields like:

- glass
- smoke
- countdown
- light versus dark
- body under pressure

Output examples:

- top imagery clusters
- recurring contrast pairs
- per-mode imagery banks

### 5. Emotional Arc Analysis

Question:

How does feeling change from section to section?

What to measure:

- emotional polarity by section
- tension build toward chorus
- vulnerability drop in bridge
- whether chorus resolves or intensifies conflict

Why it matters:

This is the difference between a flat lyric generator and one that understands dramatic movement.

Output examples:

- verse = restrained
- pre-chorus = tightening
- chorus = explosive
- bridge = exposed
- final chorus = maximal release

### 6. Narrative Perspective Analysis

Question:

Who is speaking, and from what psychological stance?

What to measure:

- first-person versus second-person presence
- direct address frequency
- self-talk versus confrontation
- internal monologue versus scene description
- certainty versus instability

Why it matters:

Two artists may use similar images but feel completely different because the speaker stance is different.

### 7. Section Function Analysis

Question:

What does each section tend to do?

What to measure:

- intro function: atmosphere, question, count-in, scene setup
- verse function: narrative detail, suppression, movement, confession
- pre-chorus function: escalation, compression, repetition
- chorus function: declaration, release, command, slogan
- bridge function: reversal, vulnerability, perspective change

Why it matters:

The generator ultimately needs not just sections, but section purpose.

### 8. Sound-Text Surface Analysis

Question:

How does the lyric feel in the mouth and ear?

What to measure:

- line length distribution
- short-line bursts versus long flowing lines
- punctuation density
- repeated syllabic shapes
- phonetic harshness versus softness
- kana/roman alphabet mixing if available later

Why it matters:

Even before audio, some artists write lyrics that feel clipped, chantable, breathless, or smooth.

This is valuable for hook generation.

## J-Pop Specific Things We Should Not Ignore

The analysis should explicitly look for:

- chorus-first identity and hook centrality
- dramatic section contrast
- image-heavy emotional writing
- code-switching level between Japanese and English
- stylized slogan phrases
- anime-opening style uplift or cinematic rise
- dark-versus-bright mood pivots

If we analyze lyrics like generic English pop text, we will miss the real signal.

## What The Analysis Output Should Become

The analysis stage should produce two downstream products.

### A. Track Analysis Document

One file per song.

Purpose:

- preserve fine-grained evidence
- make later aggregation auditable

Should include:

- track metadata
- structure summary
- repetition summary
- lexical summary
- imagery summary
- emotional arc estimate
- section function notes

### B. Artist Aggregate Profile

One file per artist.

Purpose:

- turn many track analyses into reusable style knowledge

Should include:

- dominant structural templates
- recurring imagery banks
- recurrent emotional arcs
- high-signal hook patterns
- mode candidates
- vocabulary tendencies
- constraints and anti-patterns

This artist aggregate is what should eventually feed `artists/<artist_id>/profile.json`.

## What Not To Do

Avoid these traps:

- only counting words
- relying only on sentiment scores
- flattening all sections into one bag of text
- treating every repeated word as meaningful
- mixing scraped copyrighted lyrics directly into training outputs
- jumping from normalized text straight into prompt generation without intermediate style evidence

## Minimum Viable Analysis Pipeline

If we want a practical first implementation, the order should be:

1. structure extraction
2. repetition detection
3. section-level token stats
4. imagery clustering by keyword dictionaries
5. simple emotional arc heuristics
6. artist-level aggregation across tracks

This is enough to start producing useful style signals without pretending we already have a full semantic model.

## Recommended Heuristic Outputs For V1

For each track:

- `structure_pattern`
- `section_lengths`
- `repeated_lines`
- `hook_candidates`
- `dominant_keywords`
- `imagery_tags`
- `emotion_arc_by_section`
- `pronoun_profile`
- `english_insertion_ratio`

For each artist:

- `common_structures`
- `common_chorus_shapes`
- `top_imagery_clusters`
- `top_contrast_pairs`
- `hook_pattern_summary`
- `section_role_defaults`
- `mode_candidates`

## Clear Recommendation

The next implementation should not be "AI analyzes lyrics" in a vague sense.

It should be:

1. analyze each normalized lyric into a track analysis JSON
2. aggregate many track analyses into an artist analysis JSON
3. derive the existing structured profile from that artist analysis

That is the clean bridge between lyric corpus and generation system.
