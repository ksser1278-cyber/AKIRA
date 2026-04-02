Please audit the following automated style tags and stylistic signals against current **Suno v5** and **Vocaloid/Subculture** community standards.

---

## 1. Context & Task
I am building an engine that automatically generates "Style of Music" tags and "Lyric Blueprints" for specific Vocaloid producers.

**Task**: Please analysis the generated outputs below and answer:
- Does the tag density and order follow the latest Suno v5 best practices for avoiding generic outputs?
- Are the "Rhythm Density" instructions (e.g., "high-density syllables, rapid-fire") clear directives that Suno's LLM interpreter can act upon effectively?
- Should we add any community-discovered "Vocaloid-only" tags (like `piapro`, `tuning high`, etc.) to improve the output?

## 2. Sample style Audit (PinocchioP)
From a test run for "Ironic Meta" mode:

> **Style of Music**:
> `Vocaloid, Subculture Pop, Fast tempo, High-energy, Conceptual Pop, Satirical, Fast Tempo, High Copy Pressure, Electronic-Rock Hybrid, breathless pace, synthetic tone, mechanical precision, Cynical, 120-140 BPM`

> **Slogan/Rhythm Directive**:
> `Rhythm density: high-density syllables, rapid-fire`
> `Goal: Deliver the title as a repeatable slogan (4-8 syllables). 2x repeat, with an ironic twist in the final line.`

## 3. Sample Style Audit (DECO*27)
From a test run for "Dark Cute Breakdown" mode:

> **Style of Music**:
> `Vocaloid, High-Octane Pop, Direct Emotional Rock, Cute-Toxic, Rabbit-Hole Style, High Hook Pressure, Obsessive Pop, sharp staccato, vibrant high belts, rhythmic breathing (SFX), compressed pop sheen, Intense, 120-140 BPM`

> **Slogan/Rhythm Directive**:
> `Rhythm density: maximum hook pressure, title-driven, rhythmic chant`

---

## 4. Specific Questions
1. **Exclude Tags**: What `Style Exclude` strings should we generate for **PinocchioP** to avoid "Generic Ballad" or "Emotional Human Voice" results in Suno v4?
2. **Metadata**: Are there any specific Suno v4 "Persona" or "Inspire" parameters that would help anchor these two specific producers?
