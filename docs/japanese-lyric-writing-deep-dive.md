# Japanese Lyric Writing Deep Dive

This note focuses on how professional Japanese lyric writing is commonly described in Japanese interviews, research, and music-writing commentary, with an emphasis on what matters for `AKIRA ENGINE`.

The goal is not to romanticize "Japanese songwriting" as one single method. The goal is to extract repeatable constraints that show up often enough to matter for dataset design and prompt/lyric generation.

## 1. The default professional workflow is still melody-first

One of the clearest recurring signals is that mainstream Japanese lyric writing is still heavily `kyokusen` (melody first). Junji Ishiwatari said the current industry is effectively `99.9%` melody-first, meaning lyrics are usually written to an already-existing melodic/rhythmic frame rather than as free text first.

Implication for `AKIRA ENGINE`:

- We should treat lyrics as `melody-constrained language`, not as standalone poetry.
- Generation should optimize for `fit`, `singability`, and `section function`, not just semantic richness.
- Even when we do not have the melody, we should simulate melody pressure with line-length, mora-ish counts, hook density, and section roles.

Source:

- Junji Ishiwatari interview, Asahi `and`: [https://www.asahi.com/and/m/article/15814039](https://www.asahi.com/and/m/article/15814039)

## 2. Even lyric-first writing is not "free prose"

Japanese research on lyric creation argues that even `shisen` (lyrics first) is still strongly musical. A 2025 cognitive-science paper describes lyric writing as an activity constrained by:

- total amount of text
- section-by-section text allocation
- repeated chorus shapes
- the implicit `A-melo / B-melo / Sabi` format

The paper explicitly argues that lyricists often build from `short sentences`, `effective words`, and `good-sounding phrases`, then assemble them into a "right-sized story" instead of starting with a large top-down prose narrative.

Implication for `AKIRA ENGINE`:

- Phrase-first generation is closer to Japanese practice than full-song prose drafting.
- We need reusable `phrase banks`, not only long-form section templates.
- The engine should produce and compare multiple short hook candidates before committing to full sections.

Sources:

- J-STAGE / Cognitive Studies (2025): [https://www.jstage.jst.go.jp/article/jcss/32/1/32_2024.059/_pdf](https://www.jstage.jst.go.jp/article/jcss/32/1/32_2024.059/_pdf)
- J-STAGE / melody-first process case study: [https://www.jstage.jst.go.jp/article/jaspmpms/25/0/25_19/_article/-char/ja](https://www.jstage.jst.go.jp/article/jaspmpms/25/0/25_19/_article/-char/ja)

## 3. A-melo, B-melo, and Sabi have different jobs

Japanese writing about J-pop consistently treats `A-melo / B-melo / Sabi` as creative roles, not just section labels.

The research summary above describes a common division like this:

- `A-melo`: set scene, situation, speaker, season, or social context
- `B-melo`: increase pressure and prepare the listener for the jump
- `Sabi`: deliver the central memorable line, often with repeated or near-repeated phrasing

Junji Ishiwatari also described writing `A-melo` lines that feel ambiguous at first, then become clear once the `Sabi` arrives.

Implication for `AKIRA ENGINE`:

- We should stop treating all verses as generic exposition.
- `A-melo` should usually delay full resolution.
- `B-melo` should compress language and sharpen momentum.
- `Sabi` should carry the title, slogan, or emotional release sentence.

Sources:

- J-STAGE / Cognitive Studies (2025): [https://www.jstage.jst.go.jp/article/jcss/32/1/32_2024.059/_pdf](https://www.jstage.jst.go.jp/article/jcss/32/1/32_2024.059/_pdf)
- Junji Ishiwatari interview, Asahi `and`: [https://www.asahi.com/and/m/article/15814039](https://www.asahi.com/and/m/article/15814039)

## 4. "Feels right when sung" matters more than "reads beautifully"

Japanese lyricists repeatedly describe good lyrics as something that feels natural when sung. Ishiwatari says he cares whether something feels right when sung and whether the accent position causes it to sound like a different word.

This is a major shift in emphasis:

- not just "is this line meaningful?"
- but "does this line survive the mouth?"

Implication for `AKIRA ENGINE`:

- The critic must score `singability`, not only theme coverage.
- We need penalties for lines that read like subtitles or prose.
- Hook lines should be tested for mouth-feel, accent stability, and abrupt awkward splits.

Source:

- Junji Ishiwatari interview, Asahi `and`: [https://www.asahi.com/and/m/article/15814039](https://www.asahi.com/and/m/article/15814039)

## 5. Mora matters more than English-style stress

Japanese lyrics ride on a mora-timed language. This does not mean lyricists literally count mora perfectly on paper every time, but it does mean that Japanese phrase design is strongly affected by mora-like timing and vowel endings.

Yamaha's language-and-music note explains how Japanese speakers are used to mora structure and often perceive or produce additional vowels around consonant clusters. This is important because it helps explain why Japanese lyrics respond differently to rhythmic packing than English lyrics do.

Implication for `AKIRA ENGINE`:

- We need `mora-ish` estimates per line and hook.
- Long-vowel positions, `n`, small-tsu handling, and compressed colloquial forms should be part of generation and evaluation.
- English syllable logic is a poor fit for Japanese lyric control.

Source:

- Yamaha Music Foundation / ON-KEN SCOPE: [https://www.yamaha-mf.or.jp/onkenscope/mugitaniryouko1_chapter2/](https://www.yamaha-mf.or.jp/onkenscope/mugitaniryouko1_chapter2/)

## 6. Modern Japanese pop often compresses words more aggressively

Recent Japanese lyric commentary points out that newer pop writing often prioritizes rhythmic fit and phrase impact over older, smoother J-pop treatment of words.

Junji Ishiwatari gives a concrete example:

- older J-pop might stretch `zutto` as something like three note events
- newer writing keeps it closer to two rhythmic units

He also points out the same shift for `n` handling in words like `sonna`.

This lines up with analysis of newer Japanese pop phrasing that highlights:

- more rests
- more syncopation
- denser rhythmic treatment
- more phrase fragmentation

Implication for `AKIRA ENGINE`:

- We need two Japanese phrase modes at minimum:
  - `classic_jpop_smooth`
  - `modern_jpop_compressed`
- The critic should not always reward even, symmetrical word placement.
- Some desirable hooks should land by compression and bite, not by neat meter.

Sources:

- Junji Ishiwatari on modern phrase fit: [https://www.asahi.com/and/article/20221028/423264218/](https://www.asahi.com/and/article/20221028/423264218/)
- PIA on changing Japanese pop `fuwari`: [https://lp.p.pia.jp/article/news/9295/index.html](https://lp.p.pia.jp/article/news/9295/index.html)

## 7. Spoken-speed distortion is often a strength, not a bug

PIA's analysis of aiko's phrasing is especially useful because it shows that effective Japanese lyrics are not always grid-perfect. The article points out that a phrase can work because it preserves spoken speed and mild disruption instead of aligning everything neatly.

The example matters because it shows that good Japanese lyrics often preserve:

- conversational acceleration
- local asymmetry
- slight metric disturbance

Implication for `AKIRA ENGINE`:

- "too clean" is sometimes the wrong target.
- We should allow controlled `spoken-speed compression` inside lines.
- Mild asymmetry can make a line feel more alive and less machine-laid.

Source:

- PIA on aiko's rhythmic language handling: [https://lp.p.pia.jp/article/news/89354/index.html](https://lp.p.pia.jp/article/news/89354/index.html)

## 8. Titles and hooks behave like copywriting

Japanese lyric commentary often treats the title or key hook line like a copywriting problem. Ishiwatari explicitly says lyric writing benefits from a catch-copy mindset: the writer needs a line that grabs the listener quickly.

His commentary on `Betsu no hito no kanojo ni natta yo` is especially useful because he praises it as a line that instantly creates narrative context by itself.

Implication for `AKIRA ENGINE`:

- The engine should separately score:
  - `hook copy force`
  - `title memorability`
  - `story ignition`
- A strong title/hook pair should be able to imply a situation before the whole lyric is understood.

Source:

- Ishiwatari on hook/copy force: [https://www.asahi.com/and/article/20180920/156149/](https://www.asahi.com/and/article/20180920/156149/)

## 9. Daily speech is a major phrase source

A recurring Japanese-side practice is not "invent more poetic words" but `notice better phrases`. Yasushi Akimoto says he does not aggressively chase trendy youth language; instead, he pays attention to phrases that stick in his head, especially from real conversations and stories people tell him.

His example of hearing a phrase like `wakareru riyu ga nai` and recognizing its power is important. This is not theme-first writing. It is phrase harvesting.

Implication for `AKIRA ENGINE`:

- We need a `phrase-source` field in the dataset:
  - daily speech
  - internal monologue
  - slogan-like line
  - surreal image fragment
- We should store hook candidates as isolated units, not only inside full lyrics.

Source:

- Sponichi interview with Yasushi Akimoto: [https://www.sponichi.co.jp/entertainment/news/2023/01/06/articles/20230106s00041000296000c.html](https://www.sponichi.co.jp/entertainment/news/2023/01/06/articles/20230106s00041000296000c.html)

## 10. Persona and tie-in constraints are normal, not exceptional

The J-STAGE case materials show lyric writing being guided by explicit concept sheets that include:

- singer age
- voice image
- tie-in function
- target emotional role
- section format

This matters because it means Japanese professional lyric writing is often not "write whatever you want." It is "write within a persona + function + form."

Implication for `AKIRA ENGINE`:

- `track_conditioning_record` should explicitly carry:
  - singer persona
  - tie-in function
  - audience use-case
  - structure expectation
- Style prompts should reflect not just sound, but `role in media`.

Source:

- J-STAGE / Cognitive Studies (2025): [https://www.jstage.jst.go.jp/article/jcss/32/1/32_2024.059/_pdf](https://www.jstage.jst.go.jp/article/jcss/32/1/32_2024.059/_pdf)

## 11. The practical Japanese workflow is often:

1. define performer / tie-in / section frame
2. generate many short phrase candidates
3. test which phrases feel good in the mouth
4. assign phrases to A-melo / B-melo / Sabi roles
5. adjust line length and repeated slots
6. re-read and discover story from the phrases
7. revise for title/hook force and singability

This is much closer to `assembly under constraint` than to `write an expressive poem from top to bottom`.

## 12. What this means for AKIRA ENGINE

The engine should not aim for "beautiful general lyric writing." It should aim for `Japanese melody-aware phrase assembly`.

### High-priority dataset fields

- `jp_section_role`: `a_melo`, `b_melo`, `sabi`, `dai_sabi`, `c_melo`
- `mora_estimate_per_line`
- `hook_mora_profile`
- `compressed_phrase_pattern`
- `spoken_speed_bias`
- `hook_copy_force`
- `title_ignition_score`
- `persona_constraint`
- `tie_in_function`
- `chorus_repeat_pattern`
- `phrase_source_type`
- `accent_risk_notes`

### High-priority critic checks

- does the line feel singable in Japanese?
- does the hook survive repetition?
- is the `A-melo` withholding enough?
- does the `B-melo` actually compress and ramp?
- does the `Sabi` contain a line worth repeating?
- is the title/hook relationship strong enough to trigger story?
- is the line too prose-like?
- is the phrase too smooth and generic for the intended mode?

### High-priority generation changes

- generate hooks before full lyrics
- generate `A-melo` image fragments before sentences
- allow compressed modern phrasing as an explicit mode
- score lines partly by mouth-feel and phrase bite
- use `A-melo / B-melo / Sabi` reasoning first, not generic verse/chorus prose

## Working conclusion

The most useful high-level summary is:

`Japanese professional lyric writing is usually not free-form poetry. It is melody-aware phrase design under section, persona, and repetition constraints.`

That is the level `AKIRA ENGINE` needs to model if it wants to generate lyrics and style prompts that feel more specifically J-pop, rather than just "general pop lyrics in Japanese."
