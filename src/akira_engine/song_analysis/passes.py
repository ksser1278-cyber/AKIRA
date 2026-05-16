from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .schema import EvidenceStatus, claim


SECTION_RE = re.compile(r"^\s*\[(?P<section>[^\]]+)\]\s*$")
REPEAT_RE = re.compile(r"(.{1,4})\1+")


def _song_id(raw_data: dict[str, Any]) -> str:
    return str(raw_data["song_input"].get("song_id") or raw_data["song_input"].get("title") or "unknown_song")


def _title(raw_data: dict[str, Any]) -> str:
    return str(raw_data["song_input"].get("title") or "")


def _lyrics_lines(lyrics: str) -> list[str]:
    return [line.strip() for line in lyrics.splitlines() if line.strip() and not SECTION_RE.match(line.strip())]


def _contains_any(text: str, values: list[str]) -> bool:
    lowered = text.lower()
    return any(value.lower() in lowered for value in values)


def _parse_sections(lyrics: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current = {"section": "Lyrics", "raw_lines": []}
    for raw_line in lyrics.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = SECTION_RE.match(line)
        if match:
            if current["raw_lines"]:
                sections.append(current)
            current = {"section": match.group("section"), "raw_lines": []}
            continue
        current["raw_lines"].append(line)
    if current["raw_lines"]:
        sections.append(current)
    return sections or [{"section": "Lyrics", "raw_lines": _lyrics_lines(lyrics)}]


def _surface_mood(song_input: dict[str, Any], lyrics: str) -> list[str]:
    genre = str(song_input.get("known_metadata", {}).get("genre") or song_input.get("genre") or "").lower()
    text = f"{song_input.get('title', '')} {genre} {lyrics}".lower()
    moods: list[str] = []
    if _contains_any(text, ["pop", "cute", "kawaii", "キラ", "きら", "かわいい", "sweet"]):
        moods.extend(["bright", "pop", "catchy"])
    if _contains_any(text, ["night", "夜", "rain", "雨", "city", "駅"]):
        moods.extend(["night", "urban"])
    if _contains_any(text, ["love", "愛", "恋", "好き"]):
        moods.append("romantic")
    return list(dict.fromkeys(moods or ["song-forward", "character-focused"]))


def _hidden_mood(lyrics: str) -> list[str]:
    moods: list[str] = []
    if _contains_any(lyrics, ["痛", "嫌", "毒", "壊", "死", "泣", "怖", "嘘"]):
        moods.extend(["unstable", "dark"])
    if _contains_any(lyrics, ["欲", "もっと", "全部", "だけ", "離さ", "依存"]):
        moods.append("possessive")
    if _contains_any(lyrics, ["ごめん", "弱", "寂", "ひとり", "一人"]):
        moods.append("vulnerable")
    return list(dict.fromkeys(moods or ["ambiguous", "inferable_from_context"]))


def _dominant_repeated_terms(lines: list[str], limit: int = 5) -> list[str]:
    normalized = [re.sub(r"\s+", "", line) for line in lines]
    counts = Counter(line for line in normalized if 1 <= len(line) <= 16)
    repeated = [item for item, count in counts.most_common() if count >= 2]
    if repeated:
        return repeated[:limit]
    short_repeat_hits = []
    for line in normalized:
        match = REPEAT_RE.search(line)
        if match:
            short_repeat_hits.append(match.group(0))
    return list(dict.fromkeys(short_repeat_hits))[:limit]


def analyze_identity_and_core_intent(raw_data: dict[str, Any], verified_data: dict[str, Any]) -> dict[str, Any]:
    song_input = raw_data["song_input"]
    lyrics = raw_data["lyrics"]
    lines = _lyrics_lines(lyrics)
    repeated = _dominant_repeated_terms(lines)
    surface = _surface_mood(song_input, lyrics)
    hidden = _hidden_mood(lyrics)

    speaker_type = "speaker with a defined emotional rule"
    if _contains_any(lyrics, ["僕", "私", "あたし", "俺"]):
        speaker_type = "first-person speaker whose wording carries the song identity"
    if _contains_any(lyrics, ["君", "あなた", "お前"]):
        speaker_type += " addressing a target directly"

    intent = claim(
        choice="Place a clear surface mood against a second emotional layer.",
        reason="A reusable song formula needs a visible hook surface and a deeper conflict that can drive section movement.",
        effect="The listener can remember the song quickly while still sensing tension underneath the pop surface.",
        reuse_method="Define surface_mood and hidden_mood separately before writing the hook.",
        evidence=["song_input metadata", "lyrics vocabulary", "repeated terms"],
        confidence=0.72,
        status=EvidenceStatus.INFERRED,
    )

    if repeated:
        intent["evidence"].append(f"repeated terms: {', '.join(repeated)}")

    return {
        "pass": 1,
        "name": "identity_and_core_intent",
        "song_id": _song_id(raw_data),
        "verified_metadata": verified_data,
        "core_identity": {
            "title": _title(raw_data),
            "surface_mood": surface,
            "hidden_mood": hidden,
            "speaker_type": speaker_type,
            "core_conflict": "surface appeal and inner pressure are intentionally separated",
            "main_listener_effect": "The song should be memorable first, then reveal a more specific emotional rule.",
        },
        "intent_hypothesis": [intent],
        "analysis_focus_for_next_pass": [
            "repeated phrase function",
            "speaker rule",
            "chorus judgment or catchphrase structure",
            "phonetic contrast",
        ],
    }


def _line_tags(line: str, title: str) -> list[str]:
    tags: list[str] = []
    compact = re.sub(r"\s+", "", line)
    if REPEAT_RE.search(compact) or len(compact) <= 5:
        tags.extend(["phonetic_hook", "hook_phrase"])
    if title and title in line:
        tags.append("title_reference")
    if _contains_any(line, ["僕", "私", "あたし", "俺"]):
        tags.append("persona_declaration")
    if _contains_any(line, ["君", "あなた", "お前"]):
        tags.append("target_address")
    if _contains_any(line, ["好き", "愛", "欲しい", "ほしい", "もっと"]):
        tags.append("desire_statement")
    if _contains_any(line, ["嫌", "だめ", "ダメ", "違う", "許さ", "最低"]):
        tags.append("judgment_phrase")
    if _contains_any(line, ["痛", "泣", "怖", "壊", "毒", "死"]):
        tags.append("emotional_reversal")
    if _contains_any(line, ["駅", "夜", "雨", "部屋", "街", "窓", "信号"]):
        tags.append("scene_image")
    if not tags:
        tags.append("rhythm_filler" if len(compact) <= 8 else "emotional_signal")
    return list(dict.fromkeys(tags))


def _line_analysis(line: str, *, line_index: int, title: str) -> dict[str, Any]:
    tags = _line_tags(line, title)
    if "phonetic_hook" in tags:
        choice = "Compress emotion into a short repeatable sound unit."
        intent = "Make the listener remember the mouth-feel before the full meaning."
        effect = "The line becomes easy to imitate and can function as a character hook."
        reuse = "Use a two-to-four mora repeated word when the song needs immediate recall."
    elif "judgment_phrase" in tags:
        choice = "Use a judgment phrase instead of a neutral description."
        intent = "Reveal the speaker's rule and emotional bias through a decisive phrase."
        effect = "The listener understands how the speaker evaluates the situation."
        reuse = "Let chorus or pre-chorus lines decide, reject, or classify the emotion."
    elif "scene_image" in tags:
        choice = "Anchor emotion through a concrete scene image."
        intent = "Prevent the lyric from becoming only abstract feeling."
        effect = "The listener gets a visible place or object to attach the emotion to."
        reuse = "Add one concrete object or location when a section becomes too explanatory."
    else:
        choice = "Carry the current emotional or narrative pressure forward."
        intent = "Maintain continuity between hook, speaker, and section movement."
        effect = "The line supports the song identity without forcing a new topic."
        reuse = "Keep non-hook lines tied to the same speaker rule and pressure stage."

    return {
        "line_index": line_index,
        "original_line": line,
        "translation_note": "",
        "function_tags": tags,
        "songwriting_choice": choice,
        "probable_intent": intent,
        "listener_effect": effect,
        "reuse_method": reuse,
        "status": EvidenceStatus.OBSERVED.value,
        "confidence": 0.78 if "phonetic_hook" in tags or "title_reference" in tags else 0.66,
    }


def analyze_lyrics_line_by_line(lyrics: str, identity_context: dict[str, Any]) -> dict[str, Any]:
    title = identity_context.get("core_identity", {}).get("title", "")
    sections = []
    line_index = 1
    all_tags: list[str] = []
    for section in _parse_sections(lyrics):
        analyzed_lines = []
        for line in section["raw_lines"]:
            item = _line_analysis(line, line_index=line_index, title=title)
            analyzed_lines.append(item)
            all_tags.extend(item["function_tags"])
            line_index += 1
        sections.append({"section": section["section"], "lines": analyzed_lines})

    tag_counts = Counter(all_tags)
    recommended_tags = [tag for tag, _ in tag_counts.most_common(8)]
    return {
        "pass": 2,
        "name": "line_by_line_lyric_intent",
        "song_id": identity_context["song_id"],
        "sections": sections,
        "lyric_strategy_summary": {
            "main_strategy": "Turn line-level choices into reusable function tags instead of a freeform impression.",
            "characterization_method": "Use repeated sounds, judgment phrases, and address patterns to expose the speaker.",
            "recommended_tags": recommended_tags,
            "risk": "Repeated words become childish if they do not express a speaker rule or emotional contrast.",
        },
    }


def analyze_timeline_sections(
    timeline: Any,
    lyrics_analysis: dict[str, Any],
    identity_context: dict[str, Any],
) -> dict[str, Any]:
    timeline_items: list[dict[str, Any]] = []
    if isinstance(timeline, list):
        source_items = timeline
    elif isinstance(timeline, dict) and isinstance(timeline.get("timeline"), list):
        source_items = timeline["timeline"]
    else:
        source_items = []

    if source_items:
        for index, item in enumerate(source_items, start=1):
            section = str(item.get("section") or f"Section {index}")
            timeline_items.append(
                {
                    "time_range": item.get("time_range", {"start": item.get("start", ""), "end": item.get("end", "")}),
                    "section": section,
                    "lyric_event": item.get("lyric_event", "manual timeline section"),
                    "composition_event": item.get("composition_event", "manual timeline cue"),
                    "arrangement_event": item.get("arrangement_event", "manual arrangement cue"),
                    "energy_level": item.get("energy_level", 5),
                    "vocal_density": item.get("vocal_density", 5),
                    "instrument_density": item.get("instrument_density", 5),
                    "probable_intent": item.get("probable_intent") or "Use the section to advance the song pressure.",
                    "listener_effect": item.get("listener_effect") or "The listener senses a section-level change.",
                    "status": item.get("status", EvidenceStatus.OBSERVED.value),
                    "confidence": item.get("confidence", 0.75),
                }
            )
    else:
        for index, section in enumerate(lyrics_analysis.get("sections", []), start=1):
            tags = [tag for line in section.get("lines", []) for tag in line.get("function_tags", [])]
            hook_heavy = any(tag in {"hook_phrase", "phonetic_hook", "title_reference"} for tag in tags)
            section_name = section.get("section", f"Section {index}")
            timeline_items.append(
                {
                    "time_range": {"start": "", "end": ""},
                    "section": section_name,
                    "lyric_event": "hook or catchphrase pressure" if hook_heavy else "speaker and scene development",
                    "composition_event": "not audio-verified; inferred from lyric section role",
                    "arrangement_event": "not supplied",
                    "energy_level": 7 if hook_heavy else 5,
                    "vocal_density": 8 if hook_heavy else 6,
                    "instrument_density": 0,
                    "probable_intent": "Place a memorable hook event here." if hook_heavy else "Develop the speaker rule before the next hook.",
                    "listener_effect": "The listener receives a recall point." if hook_heavy else "The listener receives context for the next payoff.",
                    "status": EvidenceStatus.INFERRED.value,
                    "confidence": 0.58,
                }
            )

    return {
        "pass": 3,
        "name": "timeline_section_analysis",
        "song_id": identity_context["song_id"],
        "timeline": timeline_items,
        "section_flow_summary": {
            "intro_role": "hook preview or scene seed",
            "verse_role": "speaker rule and detail",
            "pre_chorus_role": "pressure lift",
            "chorus_role": "hook payoff",
            "later_section_role": "variation, vulnerability, or stronger repeat",
        },
    }


def analyze_composition_arrangement_hooks(
    audio_features: Any,
    lyric_analysis: dict[str, Any],
    timeline_analysis: dict[str, Any],
) -> dict[str, Any]:
    audio = audio_features if isinstance(audio_features, dict) else {}
    bpm = audio.get("bpm")
    tempo_value = "unknown"
    tempo_confidence = 0.35
    if isinstance(bpm, (int, float)):
        tempo_value = "fast_pop" if bpm >= 135 else "mid_tempo" if bpm >= 95 else "slow_or_half_time"
        tempo_confidence = 0.85

    line_items = [line for section in lyric_analysis.get("sections", []) for line in section.get("lines", [])]
    hook_lines = [line for line in line_items if "hook_phrase" in line.get("function_tags", [])]
    phonetic_lines = [line for line in line_items if "phonetic_hook" in line.get("function_tags", [])]
    judgment_lines = [line for line in line_items if "judgment_phrase" in line.get("function_tags", [])]

    melody_strategy = claim(
        choice="Prefer compact repeatable melodic cells around the strongest lyric hooks.",
        reason="Short lyric hooks survive better when melody does not over-explain them.",
        effect="The listener remembers the phrase as a vocal gesture, not only as semantic content.",
        reuse_method="Map the main repeated phrase to a short cell and reserve longer motion for setup sections.",
        evidence=["line-level hook tags", "timeline section roles"],
        confidence=0.72,
        status=EvidenceStatus.INFERRED,
    )
    rhythm_strategy = claim(
        choice="Separate dense information sections from simpler hook sections.",
        reason="Vocaloid-adjacent writing often needs both high information flow and repeatable payoff.",
        effect="Verse can build character logic while chorus stays chantable.",
        reuse_method="Use denser verse syllables and reduce chorus syntax around the catchphrase.",
        evidence=["line function tags", "section flow summary"],
        confidence=0.7,
        status=EvidenceStatus.INFERRED,
    )
    hook_mechanism = claim(
        choice="Use phonetic repetition plus emotional or judgment contrast as the main hook engine.",
        reason="The hook becomes reusable when sound, speaker attitude, and emotional rule point at the same phrase.",
        effect="The listener can repeat the phrase while also sensing the speaker's character.",
        reuse_method="Pair a short repeated phrase with a judgment, reversal, or direct address line nearby.",
        evidence=[line.get("original_line", "") for line in hook_lines[:5]]
        or ["no explicit short hook line detected; hypothesis derived from line-function distribution"],
        confidence=0.8 if hook_lines else 0.52,
        status=EvidenceStatus.OBSERVED if hook_lines else EvidenceStatus.HYPOTHESIS,
    )
    hook_components = [
        value
        for value in [
            "short repeated phrase" if hook_lines else "",
            "phonetic repetition" if phonetic_lines else "",
            "judgment phrase" if judgment_lines else "",
            "speaker attitude",
            "section payoff",
        ]
        if value
    ]

    return {
        "pass": 4,
        "name": "composition_arrangement_hook_analysis",
        "song_id": lyric_analysis["song_id"],
        "composition_analysis": {
            "tempo_feel": {
                "value": tempo_value,
                "status": EvidenceStatus.OBSERVED.value if bpm else EvidenceStatus.HYPOTHESIS.value,
                "confidence": tempo_confidence,
                "evidence": ["audio_features.bpm"] if bpm else [],
            },
            "melody_strategy": [melody_strategy],
            "rhythm_strategy": [rhythm_strategy],
        },
        "arrangement_analysis": {
            "drums": {
                "role": "Maintain propulsion and section contrast.",
                "probable_intent": "Keep emotional material moving instead of letting it become static.",
                "listener_effect": "The song remains forward and usable as pop even when lyric content is unstable.",
                "status": EvidenceStatus.INFERRED.value,
                "confidence": 0.55 if not audio else 0.7,
            },
            "synth": {
                "role": "Support surface identity and vocal character.",
                "probable_intent": "Give the lyric hook a recognizable color and texture.",
                "listener_effect": "The hook feels like a character object rather than only a sentence.",
                "status": EvidenceStatus.INFERRED.value,
                "confidence": 0.52 if not audio else 0.68,
            },
        },
        "hook_analysis": {
            "main_hook_type": "phonetic_character_hook" if phonetic_lines else "phrase_or_judgment_hook",
            "hook_components": list(dict.fromkeys(hook_components)),
            "hook_mechanism": [hook_mechanism],
        },
    }


def build_integrated_songwriting_recipe(
    pass_1: dict[str, Any],
    pass_2: dict[str, Any],
    pass_3: dict[str, Any],
    pass_4: dict[str, Any],
) -> dict[str, Any]:
    identity = pass_1.get("core_identity", {})
    surface = ", ".join(identity.get("surface_mood", []))
    hidden = ", ".join(identity.get("hidden_mood", []))
    tags = pass_2.get("lyric_strategy_summary", {}).get("recommended_tags", [])
    has_phonetic = "phonetic_hook" in tags
    has_judgment = "judgment_phrase" in tags

    return {
        "pass": 5,
        "name": "integrated_songwriting_recipe",
        "song_id": pass_1["song_id"],
        "core_formula": {
            "one_sentence": f"Build a memorable {surface or 'surface'} layer while letting {hidden or 'inner pressure'} drive the speaker rule.",
            "songwriting_axis": "surface_identity_vs_inner_emotional_rule",
            "composition_axis": "compact_hook_cells_vs_section_pressure_development",
        },
        "lyric_formula": [
            {
                "step": 1,
                "method": "Start from a repeatable sound or catchphrase.",
                "purpose": "Give the song an immediate memory object.",
            },
            {
                "step": 2,
                "method": "Define the speaker's emotional rule.",
                "purpose": "Make the lyric feel like a character system rather than a generic topic.",
            },
            {
                "step": 3,
                "method": "Use verse for logic and chorus for judgment or catchphrase payoff.",
                "purpose": "Separate explanation from recall.",
            },
            {
                "step": 4,
                "method": "Add contrast through vulnerability, reversal, or concrete scene detail.",
                "purpose": "Prevent the song from becoming a one-note hook loop.",
            },
        ],
        "composition_formula": [
            {
                "method": "Use short repeatable cells for the main hook.",
                "purpose": "Support synthetic vocal clarity and listener recall.",
            },
            {
                "method": "Let section density change with narrative pressure.",
                "purpose": "Make A-melo, B-melo, and Sabi roles audibly distinct.",
            },
        ],
        "arrangement_formula": [
            {
                "method": "Keep the surface style clear and energetic enough to carry the hook.",
                "purpose": "Avoid making the inner emotion too heavy or static.",
            },
            {
                "method": "Keep vocal identity forward in the mix.",
                "purpose": "Let pronunciation, catchphrase, and character voice become the hook.",
            },
        ],
        "reuse_strategy": {
            "must_keep": [
                "separate surface mood from inner emotional rule",
                "clear speaker rule",
                "section-level function split",
                "evidence-backed hook mechanism",
                "choice-reason-effect-reuse claim structure",
            ],
            "can_change": [
                "surface image",
                "relationship premise",
                "tempo",
                "specific genre tags",
                "section count",
            ],
            "avoid": [
                "repeated words without character function",
                "long chorus explanations that bury the hook",
                "abstract emotion without scene or speaker rule",
                "analysis claims without evidence or confidence",
            ],
            "detected_strengths": {
                "phonetic_hook": has_phonetic,
                "judgment_phrase": has_judgment,
                "timeline_available": any(item.get("time_range", {}).get("start") for item in pass_3.get("timeline", [])),
            },
        },
    }
