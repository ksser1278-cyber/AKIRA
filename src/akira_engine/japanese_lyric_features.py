from __future__ import annotations

import re
from statistics import mean
from typing import Any

JAPANESE_CHAR_RE = re.compile(r"[\u3041-\u3096\u30a1-\u30fa\u30fc\u4e00-\u9fff]")
LATIN_CHUNK_RE = re.compile(r"[A-Za-z]+")
DIGIT_RE = re.compile(r"\d")
BREAK_PUNCTUATION = set("!?!?.,-")


def normalize_title_variants(*values: str | None) -> list[str]:
    variants: list[str] = []
    for value in values:
        raw = str(value or "").strip()
        if not raw:
            continue
        compact = "".join(ch for ch in raw if ch.isalnum() or JAPANESE_CHAR_RE.match(ch))
        for candidate in (raw, compact):
            clean = candidate.strip()
            if clean and clean not in variants:
                variants.append(clean)
    return variants


def mora_unit_estimate(text: str) -> int:
    line = str(text or "").strip()
    if not line:
        return 0
    # 1. Japanese Mora extraction (standard J-Pop rules)
    # Count all Japanese characters first (including Kanji, Hiragana, Katakana)
    chars = JAPANESE_CHAR_RE.findall(line)
    raw_count = len(chars)
    # Subtract Yōon markers (small kana: ゃゅょゎ ャュョヮ) as they combine with the preceding character to form 1 Mora
    yoon_markers = re.findall(r"[ゃゅょゎャュョヮ]", line)
    mora_count = raw_count - len(yoon_markers)
    
    # 2. Latin/English blocks (heuristic: 2 chars = 1 beat for J-Pop)
    latin_units = sum(max(1, len(chunk) // 2) for chunk in LATIN_CHUNK_RE.findall(line))
    # 3. Digits and Punctuation
    digit_units = len(DIGIT_RE.findall(line))
    punctuation_units = sum(1 for ch in line if ch in BREAK_PUNCTUATION)
    
    return max(0, mora_count + latin_units + digit_units + punctuation_units)


def classify_mora_density(lines: list[str]) -> str:
    units = [mora_unit_estimate(line) for line in lines if str(line).strip()]
    if not units:
        return "balanced"
    average = mean(units)
    if average <= 8:
        return "sparse"
    if average <= 14:
        return "balanced"
    if average <= 20:
        return "dense"
    return "compressed"


def classify_spoken_speed(lines: list[str]) -> str:
    units = [mora_unit_estimate(line) for line in lines if str(line).strip()]
    if not units:
        return "medium"
    short_ratio = sum(1 for value in units if value <= 8) / len(units)
    break_hits = sum(sum(1 for ch in line if ch in BREAK_PUNCTUATION) for line in lines)
    if short_ratio >= 0.45 or break_hits >= max(2, len(lines)):
        return "high"
    if short_ratio >= 0.2 or break_hits >= 1:
        return "medium"
    return "low"


def infer_jp_section_role(section_type: str, section_name: str, index: int, total: int) -> str:
    kind = str(section_type or "").strip().lower()
    name = str(section_name or "").strip().lower()
    if kind == "intro":
        return "intro"
    if kind == "verse":
        return "a_melo"
    if kind == "pre_chorus":
        return "b_melo"
    if kind == "chorus":
        if "final" in name or "last" in name or index == total - 1:
            return "dai_sabi"
        return "sabi"
    if kind == "bridge":
        return "c_melo"
    if kind == "outro":
        return "outro"
    return "other"


def infer_phrase_energy_role(section_type: str, jp_section_role: str) -> str:
    kind = str(section_type or "").strip().lower()
    if jp_section_role == "a_melo":
        return "observation"
    if jp_section_role == "b_melo":
        return "compression"
    if jp_section_role in {"sabi", "dai_sabi"}:
        return "release"
    if jp_section_role == "c_melo":
        return "pivot"
    if kind == "outro":
        return "afterglow"
    return "observation"


def infer_title_drop_role(lines: list[str], title_variants: list[str], *, late_section: bool = False) -> str:
    if not title_variants:
        return "none"
    joined = " ".join(str(line) for line in lines)
    full_hits = [variant for variant in title_variants if variant and variant in joined]
    if full_hits:
        return "reframe" if late_section else "full"
    split_tokens: list[str] = []
    for variant in title_variants:
        split_tokens.extend(token for token in re.split(r"[\s\-_/]+", variant) if len(token) >= 2)
    split_tokens = list(dict.fromkeys(split_tokens))
    if any(token in joined for token in split_tokens):
        return "foreshadow" if not late_section else "partial"
    return "none"


def estimate_hook_copy_force(hook_lines: list[str], title_variants: list[str]) -> str:
    lines = [str(line).strip() for line in hook_lines if str(line).strip()]
    if not lines:
        return "low"
    units = [mora_unit_estimate(line) for line in lines]
    avg_units = mean(units)
    repetition = len(lines) - len(set(lines))
    title_hits = sum(1 for variant in title_variants if variant and any(variant in line for line in lines))
    short_line_hits = sum(1 for value in units if value <= 10)
    if (title_hits >= 1 and short_line_hits >= 1) or repetition >= 1 or avg_units <= 10:
        return "high"
    if avg_units <= 15 or short_line_hits >= 1:
        return "medium"
    return "low"


def infer_title_ignition_style(section_entries: list[dict[str, Any]], title_variants: list[str]) -> str:
    first_hit_index: int | None = None
    first_hit_role = ""
    last_index = len(section_entries) - 1
    for index, entry in enumerate(section_entries):
        lines = entry.get("lines") or entry.get("section_lines") or []
        role = entry.get("jp_section_role") or infer_jp_section_role(entry.get("section_type", ""), entry.get("section_name", ""), index, len(section_entries))
        drop = infer_title_drop_role(lines, title_variants, late_section=index >= max(1, last_index - 1))
        if drop != "none":
            first_hit_index = index
            first_hit_role = role
            break
    if first_hit_index is None:
        return "hidden"
    if first_hit_index <= 1:
        return "immediate"
    if first_hit_role in {"dai_sabi", "outro"}:
        return "reframing"
    return "delayed"


def infer_phrase_source_types(record: dict[str, Any]) -> list[str]:
    sources: list[str] = []
    thesis = str(record.get("song_intent", {}).get("emotional_thesis", "")).lower()
    motifs = [str(item).lower() for item in record.get("song_intent", {}).get("key_motifs", [])]
    roles = [str(item).lower() for item in record.get("song_intent", {}).get("narrative_role", [])]
    hook_lines = [str(item) for item in record.get("lyric_ground_truth", {}).get("hook_lines", [])]

    if any(term in thesis for term in ("i ", "my ", "self", "heart", "emotion")) or any("confession" in role or "self" in role for role in roles):
        sources.append("internal_monologue")
    if any(term in thesis for term in ("city", "night", "room", "body", "gaze")):
        sources.append("scene_fragment")
    if any(term in motif for motif in motifs for term in ("chart", "scalpel", "heartbeat", "diagnosis", "error")):
        sources.append("concept_metaphor")
    if hook_lines and estimate_hook_copy_force(hook_lines, normalize_title_variants(record.get("track_identity", {}).get("title"), record.get("track_identity", {}).get("title_core"))) in {"medium", "high"}:
        sources.append("copy_line")
    if not sources:
        sources.append("internal_monologue")
    return list(dict.fromkeys(sources))


def infer_modern_compression_bias(section_entries: list[dict[str, Any]]) -> str:
    densities = [entry.get("mora_density") for entry in section_entries]
    spoken = [entry.get("spoken_speed_bias") for entry in section_entries]
    if densities.count("compressed") >= 2 or spoken.count("high") >= 2:
        return "high"
    if "dense" in densities or "high" in spoken or "medium" in spoken:
        return "medium"
    return "low"


def build_japanese_lyric_profile(record: dict[str, Any]) -> dict[str, Any]:
    sections = record.get("lyric_ground_truth", {}).get("sections", [])
    section_entries: list[dict[str, Any]] = []
    for index, section in enumerate(sections):
        role = infer_jp_section_role(section.get("section_type", ""), section.get("section_name", ""), index, len(sections))
        section_entries.append(
            {
                "section_name": section.get("section_name", f"Section {index + 1}"),
                "section_type": section.get("section_type", "other"),
                "lines": section.get("lines", []),
                "jp_section_role": role,
                "mora_density": classify_mora_density(section.get("lines", [])),
                "spoken_speed_bias": classify_spoken_speed(section.get("lines", [])),
                "phrase_energy_role": infer_phrase_energy_role(section.get("section_type", ""), role),
            }
        )

    title_variants = normalize_title_variants(
        record.get("track_identity", {}).get("title"),
        record.get("track_identity", {}).get("title_core"),
    )
    for index, section in enumerate(section_entries):
        section["title_drop_role"] = infer_title_drop_role(
            section["lines"],
            title_variants,
            late_section=index >= max(1, len(section_entries) - 2),
        )

    hook_copy_force = estimate_hook_copy_force(
        record.get("lyric_ground_truth", {}).get("hook_lines", []),
        title_variants,
    )
    modern_compression_bias = infer_modern_compression_bias(section_entries)
    title_ignition_style = infer_title_ignition_style(section_entries, title_variants)
    phrase_source_types = infer_phrase_source_types(record)

    mora_notes = [
        f"{entry['section_name']}: {entry['mora_density']}"
        for entry in section_entries
        if entry["mora_density"] in {"dense", "compressed"}
    ]
    accent_risk_notes: list[str] = []
    if any("copy_line" in source for source in phrase_source_types) and hook_copy_force == "high":
        accent_risk_notes.append("High-copy hook should be checked against actual melodic accent placement before reuse.")
    if modern_compression_bias == "high":
        accent_risk_notes.append("Compressed modern phrasing likely needs manual singability review.")

    critic_focus = ["section_role_clarity", "hook_copy_force", "mora_density_control"]
    if modern_compression_bias in {"medium", "high"}:
        critic_focus.append("spoken_speed_bias")
    if title_ignition_style in {"delayed", "reframing"}:
        critic_focus.append("title_drop_timing")

    return {
        "workflow_bias": "unknown",
        "hook_copy_force": hook_copy_force,
        "title_ignition_style": title_ignition_style,
        "modern_compression_bias": modern_compression_bias,
        "phrase_source_types": phrase_source_types,
        "mora_control_notes": mora_notes,
        "accent_risk_notes": accent_risk_notes,
        "critic_focus": critic_focus,
        "section_features": [
            {
                key: value
                for key, value in entry.items()
                if key != "lines"
            }
            for entry in section_entries
        ],
    }


def build_markdown_japanese_profile(title: str, markdown_text: str) -> dict[str, Any]:
    section_entries: list[dict[str, Any]] = []
    current_name = ""
    current_lines: list[str] = []

    def flush_section() -> None:
        if not current_name:
            return
        normalized = current_name.strip("[]").strip().lower()
        section_type = normalized
        if normalized.startswith("verse"):
            section_type = "verse"
        elif normalized.startswith("pre_chorus"):
            section_type = "pre_chorus"
        elif normalized.startswith("chorus"):
            section_type = "chorus"
        elif normalized.startswith("bridge"):
            section_type = "bridge"
        elif normalized.startswith("intro"):
            section_type = "intro"
        elif normalized.startswith("outro"):
            section_type = "outro"
        section_entries.append(
            {
                "section_name": current_name.strip("[]"),
                "section_type": section_type,
                "lines": current_lines[:],
            }
        )

    for raw_line in str(markdown_text).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("# "):
            continue
        if line.startswith("[") and line.endswith("]"):
            flush_section()
            current_name = line
            current_lines = []
            continue
        current_lines.append(line)
    flush_section()

    record = {
        "track_identity": {"title": title, "title_core": title},
        "lyric_ground_truth": {
            "sections": section_entries,
            "hook_lines": [line for entry in section_entries if entry["section_type"] == "chorus" for line in entry["lines"][:2]],
        },
        "song_intent": {},
    }
    return build_japanese_lyric_profile(record)
