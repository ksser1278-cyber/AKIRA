# Universal J-Pop Songwriting Blueprint (AKIRA ENGINE Spec v1.0)

This blueprint codifies the statistical "Golden Rules" extracted from the Alexandria 60k Mastery Analysis (Elite vs. Control). These rules are to be treated as mandatory constraints for the `songwriter_v2` and `lyric_draft` pipelines.

---

## 1. Structural Architecture (The "Elite Lift" Framework)

### [Rule 1A] The Repetition Hooking (High-Fidelity Repetition)

- **Constraint**: Each major section (Verse, Chorus) MUST contain at least **one internal repetition** of a line or a sub-phrase.
- **Metric**: Target Sectional Repetition Index: **0.027 - 0.035**.
- **Execution**: Do not generate 100% unique lines. Use "A-B-A-C" or "A-A-B-B" structures to enforce hook recall.

### [Rule 1B] Rhythmic Tension (Line Variance)

- **Constraint**: Line lengths MUST NOT be uniform.
- **Metric**: Target Mora Variance: **> 3.3**.
- **Execution**: Alternate short "impact" lines (4-6 mora) with long "dense" lines (12-16 mora). Avoid the "Mid-range monotone" (all lines 8-10 mora).

### [Rule 1C] Hook Return Latency (Modern Speed)

- **Constraint**: The first [Chorus] MUST start before line 10.
- **Metric**: Target Latency: **8-9 lines**.
- **Execution**: Keep Intro and Verse 1 lean. If Verse 1 exceeds 8 lines, split it or move to Pre-Chorus by line 6.

---

## 2. Phonetic & Lexical Mechanics

### [Rule 2A] The 15-Mora Sabi (Density Peak)

- **Constraint**: Chorus lines MUST target a mean density of **15 mora**.
- **Metric**: Chorus Mora Density: **14.5 - 15.5**.
- **Execution**: Pack the chorus. Use compound Kanji and multi-syllable Katakana to hit the density target without losing singability.

### [Rule 2B] Vowel Dominance (Brilliance Filter)

- **Constraint**: Chorus sections MUST prioritize 'A' and 'I' vowels (Brilliance/Impact).
- **Metric**: Vowel Ratio: **A > I > O > E > U**.
- **Execution**: Ending lines on 'A' or 'I' (High energy) is preferred over 'U' (Low energy/Closed).

### [Rule 2C] Impact Suppression (Smooth Flow)

- **Constraint**: Elite tracks favor "Smooth" flow over "Harsh" plosives.
- **Metric**: Phonetic Impact Index: **0.14 - 0.15** (Avoid exceeding 0.17).
- **Execution**: Use fricatives and nasals (S, N, M) to connect dense mora blocks. Avoid "staccato overload" unless explicitly requested (e.g., glitch-hop style).

---

## 3. Integration Guidelines (Engine Prompting)

When the engine generates a song plan, it must inject these constants:

- `structure_tension_min: 3.3`
- `chorus_density_target: 15.0`
- `repetition_policy: "strict_hooking"`
- `vowel_priority: ["a", "i"]`

---

## 4. Anti-Patterns (The "Control Group" Trap)

- **Uniformity**: Every line being 10 mora (The "Mid-track" curse).
- **No-Repetitions**: Every line is unique (Low hook retention).
- **Delayed Chorus**: Starting Sabi at line 12+ (Modern "Skipped" track risk).
- **U-Vowel Dominance**: Closing hooks on 'u' or 'o' exclusively (Muted resonance).

---

> [!IMPORTANT]
> This Spec replaces all previous "Artist-specific" heuristics. Artist profiles should now act as **shaping filters** on top of this Universal Baseline.
