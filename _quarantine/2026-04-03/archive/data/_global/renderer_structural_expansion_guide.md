# Renderer Structural Expansion Guide (AKIRA ENGINE)

This guide provides the specific patterns and logic branches to be implemented in `demo_renderer.py` to move beyond the current "Generic Templating" and capture the unique phrase shaping of each core artist.

## 1. Targeted Expansion Areas in `demo_renderer.py`

### A. `_artist_verse_lines` (Line 96+)

Currently, many artists (e.g. Kairiki Bear, Syudou, Neru) fall through to mode-level defaults.

- [ ] **Kairiki Bear:** Implement iterative phonetic loops.
  - *Pattern:* `f"{a}が　{a}が　止まる 止まる"`, `f"{b}に　なり なる なる なる"`
- [ ] **Syudou:** Implement diagnostic interjection prefixes.
  - *Pattern:* `f"【診断：{a}】　{b}ばかり見てる 僕だ"`, `f"いっそ {c}ごと 笑い飛ばせば"`

### B. `_artist_chorus_lines` (Line 191+)

The current "Hook Hook" pattern is effective but needs artist-specific variation in the 2nd and 3rd lines.

- [ ] **Kanaria (Title Drop Logic):**
  - *Pattern:* `f"{hook}こそが 正体(あかし)"`, `f"その{a}で 余裕を 塗りつぶして"`
- [ ] **Neru (Industrial Imperative):**
  - *Pattern:* `f"{hook}　{hook}　ぶっ壊せ"`, `f"その{a}を 手術台に 載せろ"`

## 2. Low-Cost Strategy: Phrase Pattern Injection

Instead of hardcoding every line, use the `a, b, c` slots more aggressively with artist-specific "Glue Text".

### Example: Maretu's Polite-Cruelty Shift

Modify the `maretu` branch in `_artist_verse_lines`:

```python
if artist_id == "maretu":
    return [
        f"どうか {a}だけは 綺麗なまま 腐らせて",  # Keigo-Dissonance
        f"{b}を選ぶたび まともさだけが 剥がれていく",
        f"{c}みたいな 倫理の 掃き溜めで", # Industrial Motif
        "やさしい言葉ほど 最後に 毒へ変わる",
    ]
```

## 3. Review Checklist for Implementation

- [ ] **Slot Parity:** Ensure every new branch consumes `a`, `b`, and `hook`.
- [ ] **Mora Check:** Keep line lengths below 24 characters for singability.
- [ ] **Particle Integrity:** Use Japanese particles exclusively (`が`, `を`, `に`). No script mix.

## 4. Triage Mapping

- **If "Generic" signal recurs:** Increase the frequency of `hook` reuse in the verse.
- **If "Jitter" occurs in Kairiki Bear:** Fix the repetition spacing (e.g. `なり なる なる なる` vs `なりなるなるなる`).

---
**Status:** implementation-ready
**Reference:** [Renderer Follow-up Triage](renderer_followup_triage.md)
