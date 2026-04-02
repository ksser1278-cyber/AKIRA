# [TRI-COUNSEL BRIEF] - High-Fidelity Style Pipeline (v1.0)

This brief is for synchronization across the **Tri-Counsel** (Antigravity, Gemini Web, GPT).

---

## 1. Antigravity's Action (Local)
I have successfully implemented and verified the high-fidelity stylistic rules for **PinocchioP** and **DECO*27** within the engine.

- **Updated**: [src/akira_engine/generator.py](file:///c:/JPop_Songwriter/AKIRA%20ENGINE/src/akira_engine/generator.py) (Resilience, Structure Merging, High-Fidelity fields).
- **Normalized**: Artist [profile.json](file:///c:/JPop_Songwriter/AKIRA%20ENGINE/artists/ado/profile.json) files for both producers.
- **Verified**: Generated test packages for `ironic_meta` (PinocchioP) and `dark_cute_breakdown` (DECO*27).

## 2. Problem / Logic
The "High-Fidelity" layer bridges the gap between static profiles and dynamic songwriting. 

1. **Rhythm Density**: Injected at the section level to control syllable speed (crucial for Vocaloid "breathless" vs "rhythmic" contrast).
2. **Negative Constraints**: Prevents the LLM from "polluting" the style with generic ballad or confession tropes.
3. **Structure Merging**: Dynamically pulls section goals from [structure_profile.json](file:///c:/JPop_Songwriter/AKIRA%20ENGINE/artists/ado/structure_profile.json) to ensure the song follows the correct structural logic (e.g., slogan-hooks for PinocchioP).

## 3. Request for Gemini Web (Trends & Context)
> [!IMPORTANT]
> **Task**: Review the generated style tags and section goals against **Suno v4 Vocaloid Prompting** trends.
> 
> - Does "Rhythm Density" (high-density syllables vs low-density slogans) map effectively to Suno's current interpretation of Vocaloid genres?
> - Are there any new "Vocaloid-specific" tags or exclude-constraints recently discovered by the community for Suno v4 that we should add to our [base_style_tags](file:///c:/JPop_Songwriter/AKIRA%20ENGINE/src/akira_engine/profile_builder.py#133-148)?

## 4. Request for GPT (Logic & Stylistic Review)
> [!WARNING]
> **Task**: Review the stylistic logic and negative constraints for **consistency**.
> 
> - **PinocchioP**: Are the "Ironic Meta" writing principles ("cute surface, toxic meaning") and negative constraints ("no earnest confession") sufficient to prevent "Human-Pop" contamination?
> - **DECO*27**: Does the "Direct Address" focus and "Somatic Metaphors" correctly capture the essence of his modern style (e.g., Rabbit Hole, Vampire)?
> - **Code Review**: Check the [generator.py](file:///c:/JPop_Songwriter/AKIRA%20ENGINE/src/akira_engine/generator.py) fallback logic (using imagery bank as title seeds) for potential edge-case failures.

## 5. Local Context Snapshot (For Copying)

### [PinocchioP Profile Snippet]
```json
{
  "writing_principles": [
    "cute surface, toxic meaning",
    "ironic self-awareness",
    "compressed slogan hooks"
  ],
  "negative_constraints": [
    "no earnest emotional confession",
    "no pure romance focus",
    "avoid excessive sincerity"
  ],
  "rhythm_density": {
    "verse": "high-density syllables, rapid-fire",
    "chorus": "low density per line, short and punchy repetition"
  }
}
```

### [DECO*27 Profile Snippet]
```json
{
  "writing_principles": [
    "direct address ('You' and 'I' focus)",
    "title-first hook binding",
    "somatic metaphors (biting, eating, breathing)"
  ],
  "rhythm_density": {
    "verse": "syncopated, rhythmic, medium density",
    "chorus": "maximum hook pressure, title-driven, rhythmic chant"
  }
}
```
