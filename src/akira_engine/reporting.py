from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MODE_EXPLANATIONS = {
    "rebellious_dark": "dark pressure, fracture imagery, and a forceful release",
    "night_drive": "urban night motion and restless forward energy",
    "anthemic_cinematic": "light-versus-dark contrast with a rising final lift",
    "intimate_confessional": "private first-person pressure and inward detail",
}


def is_unlabeled_label(label: str) -> bool:
    return label.startswith("unlabeled") or label == "untitled"


def contains_meaningful_section_labels(section_names: list[str]) -> bool:
    return any(not is_unlabeled_label(name) for name in section_names)


@dataclass
class ReportSummary:
    output_path: Path
    artist_id: str


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_utf8_text(path: Path, content: str, trailing_newline: bool = True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = content if not trailing_newline or content.endswith("\n") else content + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def write_utf8_json(path: Path, payload: dict[str, Any]) -> Path:
    return write_utf8_text(path, json.dumps(payload, ensure_ascii=False, indent=2), trailing_newline=True)


def discover_track_files(track_root: Path, artist_id: str) -> list[Path]:
    artist_dir = track_root / artist_id
    if not artist_dir.exists():
        return []
    return sorted(path for path in artist_dir.glob("*.json") if path.is_file())


def take_values(items: list[dict[str, Any]], key: str, limit: int) -> list[Any]:
    return [item[key] for item in items[:limit] if key in item]


def join_words(words: list[str]) -> str:
    if not words:
        return ""
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return f"{words[0]} and {words[1]}"
    return f"{', '.join(words[:-1])}, and {words[-1]}"


def one_line_read(artist_analysis: dict[str, Any]) -> str:
    imagery = take_values(artist_analysis["imagery_profile"]["top_imagery_clusters"], "tag", 3)
    arc = take_values(artist_analysis["emotional_profile"]["dominant_arc_patterns"], "arc", 1)
    perspective = artist_analysis["vocabulary_profile"]["pronoun_profile"]["dominant_perspective"]
    hook_sections = take_values(artist_analysis["hook_pattern_summary"]["common_hook_sections"], "section", 2)

    perspective_phrase = {
        "first_person": "first-person",
        "second_person": "direct-address",
        "third_person": "observational",
        "undetermined": "voice-driven",
    }.get(perspective, "voice-driven")

    imagery_phrase = join_words([tag.replace("_", " ") for tag in imagery]) or "strong recurring imagery"
    arc_phrase = arc[0].replace("_", " ") if arc else "clear section contrast"
    if hook_sections and contains_meaningful_section_labels(hook_sections):
        hook_phrase = join_words(hook_sections)
    else:
        hook_phrase = "repeated stanza clusters"
    return (
        f"This reads like {perspective_phrase} J-Pop writing built on {imagery_phrase}, "
        f"with the strongest payoff landing in {hook_phrase} and an overall {arc_phrase} shape."
    )


def artist_feel_paragraph(artist_analysis: dict[str, Any]) -> str:
    imagery_terms = take_values(artist_analysis["imagery_profile"]["top_imagery_terms"], "term", 6)
    modes = take_values(artist_analysis["mode_candidates"], "mode", 3)
    mode_phrases = [MODE_EXPLANATIONS.get(mode, mode.replace("_", " ")) for mode in modes]
    return (
        f"The lyric world clusters around {join_words(imagery_terms)}. "
        f"As a vibe, it leans toward {join_words(mode_phrases)}."
    )


def emotional_flow_lines(artist_analysis: dict[str, Any]) -> list[str]:
    meaningful_sections = [
        section for section in artist_analysis["section_role_defaults"]
        if not is_unlabeled_label(section["section"])
    ]
    if not meaningful_sections:
        return [
            "- Source lyrics are mostly stanza-formatted rather than explicitly marked as verse/chorus.",
            "- Emotional defaults are therefore more reliable at the whole-song level than at named section labels.",
        ]

    lines: list[str] = []
    for section in meaningful_sections:
        emotions = take_values(section["common_emotions"], "emotion", 1)
        functions = take_values(section["common_functions"], "function", 2)
        emotion_phrase = emotions[0].replace("_", " ") if emotions else "neutral"
        function_phrase = ", ".join(item.replace("_", " ") for item in functions) if functions else "general support"
        lines.append(
            f"- `{section['section']}` feels like {emotion_phrase} and usually acts as {function_phrase}."
        )
    return lines


def hook_lines(track_analyses: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    lines: list[str] = []
    for track in track_analyses:
        for hook in track["repetition"]["hook_candidates"]:
            line = hook["line"]
            key = line.lower()
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"- `{line}`")
            if len(lines) >= 5:
                return lines
    return lines


def track_snapshot(track: dict[str, Any]) -> list[str]:
    imagery = take_values(track["imagery"]["imagery_tags"], "tag", 4)
    repeated_openings = take_values(track["repetition"]["repeated_openings"], "opening", 3)
    dominant_arc = track["emotion_arc"]["overall_arc_label"].replace("_", " ")
    section_labels = track["structure"]["section_order"]
    if contains_meaningful_section_labels(section_labels):
        structure_line = f"`{track['structure']['structure_pattern']}`"
    else:
        structure_line = f"{track['structure']['section_count']} stanza blocks (source layout)"
    return [
        f"### {track['title']}",
        f"- Structure: {structure_line}",
        f"- Core imagery: {join_words([item.replace('_', ' ') for item in imagery])}",
        f"- Emotional movement: {dominant_arc}",
        f"- Repeated entry points: {join_words(repeated_openings) if repeated_openings else 'none'}",
    ]


def mode_read_lines(artist_analysis: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for mode in artist_analysis["mode_candidates"][:4]:
        explanation = MODE_EXPLANATIONS.get(mode["mode"], mode["mode"].replace("_", " "))
        lines.append(
            f"- `{mode['mode']}`: score {mode['score']} -> {explanation}"
        )
    return lines


def render_report(artist_analysis: dict[str, Any], track_analyses: list[dict[str, Any]]) -> str:
    imagery_tags = take_values(artist_analysis["imagery_profile"]["top_imagery_clusters"], "tag", 5)
    hook_sections = take_values(artist_analysis["hook_pattern_summary"]["common_hook_sections"], "section", 3)
    dominant_tokens = take_values(artist_analysis["vocabulary_profile"]["top_tokens"], "token", 8)
    if hook_sections and not contains_meaningful_section_labels(hook_sections):
        hook_section_summary = "repeated stanza clusters"
    else:
        hook_section_summary = join_words(hook_sections) if hook_sections else "not enough data yet"

    lines = [
        f"# {artist_analysis['artist_name']} Style Report",
        "",
        "## One-Line Read",
        one_line_read(artist_analysis),
        "",
        "## Artist Feel",
        artist_feel_paragraph(artist_analysis),
        "",
        "## What Stands Out",
        f"- Dominant imagery clusters: {join_words([item.replace('_', ' ') for item in imagery_tags])}",
        f"- Hook-heavy zones: {hook_section_summary}",
        f"- Frequent lexical anchors: {join_words(dominant_tokens) if dominant_tokens else 'not enough data yet'}",
        "",
        "## Emotional Flow",
    ]

    lines.extend(emotional_flow_lines(artist_analysis))
    lines.extend(
        [
            "",
            "## Hook Examples",
        ]
    )
    lines.extend(hook_lines(track_analyses) or ["- not enough hook evidence yet"])
    lines.extend(
        [
            "",
            "## Mode Read",
        ]
    )
    lines.extend(mode_read_lines(artist_analysis))
    lines.extend(
        [
            "",
            "## Track Snapshots",
        ]
    )
    if track_analyses:
        for track in track_analyses:
            lines.extend(track_snapshot(track))
            lines.append("")
    else:
        lines.append("No track analyses were found for this artist.")
        lines.append("")

    lines.extend(
        [
            "## Interpretation Note",
            "This report is meant for human intuition. It translates analysis evidence into vibe-level language rather than raw JSON fields.",
            "",
        ]
    )
    return "\n".join(lines)


def default_output_path(artist_analysis: dict[str, Any]) -> Path:
    return Path("reports") / "style" / f"{artist_analysis['artist_id']}_style_report.md"


def render_artist_report(
    artist_analysis_path: Path,
    track_analysis_root: Path,
    output_path: Path | None = None,
) -> ReportSummary:
    artist_analysis = load_json(artist_analysis_path)
    track_files = discover_track_files(track_analysis_root, artist_analysis["artist_id"])
    track_analyses = [load_json(path) for path in track_files]
    report = render_report(artist_analysis, track_analyses)
    final_path = output_path or default_output_path(artist_analysis)
    write_utf8_text(final_path, report, trailing_newline=True)
    return ReportSummary(output_path=final_path, artist_id=artist_analysis["artist_id"])
