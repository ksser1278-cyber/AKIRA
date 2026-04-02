from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from .dataset import build_records_from_seed_file
from .generator import load_profile, resolve_mode


@dataclass
class ArtistEvaluationSummary:
    report_path: Path
    total_records: int
    average_score: float
    strong_records: int


def tokenize(value: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) > 2]


def collect_creative_output_text(record: dict[str, Any]) -> str:
    blueprint = record["target_blueprint"]
    chunks = []
    chunks.extend(blueprint["title_ideas"])
    chunks.extend(blueprint["hook_ideas"])
    chunks.extend(section["prompt"] for section in blueprint["section_blueprint"])
    return " ".join(chunks).lower()


def collect_surface_output_text(record: dict[str, Any]) -> str:
    blueprint = record["target_blueprint"]
    chunks = []
    chunks.extend(blueprint["title_ideas"])
    chunks.extend(blueprint["hook_ideas"])
    return " ".join(chunks).lower()


def theme_coverage_score(record: dict[str, Any]) -> float:
    theme_tokens = tokenize(record["input_context"]["theme"])
    if not theme_tokens:
        return 1.0
    output_text = collect_surface_output_text(record)
    hits = sum(1 for token in theme_tokens if token in output_text)
    return hits / len(theme_tokens)


def emotion_coverage_score(record: dict[str, Any]) -> float:
    emotion = record["input_context"]["emotion"].lower()
    output_text = collect_surface_output_text(record)
    style_text = record["target_blueprint"]["style_of_music"].lower()
    return 1.0 if emotion in output_text or emotion in style_text else 0.0


def keyword_coverage_score(record: dict[str, Any]) -> float:
    keywords = [keyword.lower() for keyword in record["input_context"].get("keywords", [])]
    if not keywords:
        return 1.0
    output_text = collect_surface_output_text(record)
    hits = sum(1 for keyword in keywords if keyword in output_text)
    return hits / len(keywords)


def mode_alignment_score(profile: dict[str, Any], record: dict[str, Any]) -> float:
    mode = resolve_mode(profile, record["mode_id"])
    style_text = record["target_blueprint"]["style_of_music"].lower()
    required_tags = [tag.lower() for tag in mode["style_tags"]]
    hits = sum(1 for tag in required_tags if tag in style_text)
    return hits / len(required_tags) if required_tags else 1.0


def structure_score(profile: dict[str, Any], record: dict[str, Any]) -> float:
    mode = resolve_mode(profile, record["mode_id"])
    expected_sections = [section["section"] for section in mode["section_blueprint"]]
    actual_sections = [
        section["section"] for section in record["target_blueprint"]["section_blueprint"]
    ]
    hits = sum(1 for section in expected_sections if section in actual_sections)
    return hits / len(expected_sections) if expected_sections else 1.0


def safety_score(profile: dict[str, Any], record: dict[str, Any]) -> float:
    artist_name = profile["display_name"].lower()
    output_text = collect_surface_output_text(record)
    creative_fields = output_text
    if artist_name in creative_fields:
        return 0.0
    blocked_terms = [
        term.lower()
        for term in profile["lyric_rules"]["avoid_terms"]
        if term.lower() != "direct artist naming"
    ]
    violations = sum(1 for term in blocked_terms if term in creative_fields)
    return 1.0 if violations == 0 else 0.0


def score_record(profile: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    theme_score = theme_coverage_score(record)
    emotion_score = emotion_coverage_score(record)
    keyword_score = keyword_coverage_score(record)
    mode_score = mode_alignment_score(profile, record)
    section_score = structure_score(profile, record)
    safety = safety_score(profile, record)

    total_score = round(
        (
            theme_score * 20
            + emotion_score * 15
            + keyword_score * 20
            + mode_score * 15
            + section_score * 15
            + safety * 15
        ),
        2,
    )
    return {
        "record_id": record["record_id"],
        "mode_id": record["mode_id"],
        "theme": record["input_context"]["theme"],
        "emotion": record["input_context"]["emotion"],
        "scores": {
            "theme": round(theme_score, 2),
            "emotion": round(emotion_score, 2),
            "keywords": round(keyword_score, 2),
            "mode_alignment": round(mode_score, 2),
            "structure": round(section_score, 2),
            "safety": round(safety, 2),
            "total": total_score,
        },
    }


def score_label(total_score: float) -> str:
    if total_score >= 90:
        return "strong"
    if total_score >= 75:
        return "usable"
    return "weak"


def render_report(profile: dict[str, Any], record_scores: list[dict[str, Any]]) -> str:
    average_score = round(
        sum(item["scores"]["total"] for item in record_scores) / len(record_scores), 2
    )
    strong_records = sum(1 for item in record_scores if item["scores"]["total"] >= 90)
    usable_records = sum(
        1 for item in record_scores if 75 <= item["scores"]["total"] < 90
    )
    weak_records = sum(1 for item in record_scores if item["scores"]["total"] < 75)

    lines = [
        f"# {profile['display_name']} Single-Artist Quality Report",
        "",
        "## Summary",
        f"- Artist: {profile['display_name']}",
        f"- Total records reviewed: {len(record_scores)}",
        f"- Average heuristic score: {average_score}/100",
        f"- Strong records: {strong_records}",
        f"- Usable records: {usable_records}",
        f"- Weak records: {weak_records}",
        "",
        "## Interpretation",
        "- This score reflects blueprint quality, not final sung audio quality.",
        "- High scores mean the generated blueprint is structurally aligned, on-theme, and respects style constraints.",
        "",
        "## Record Scores",
    ]

    for item in record_scores:
        scores = item["scores"]
        lines.extend(
            [
                f"### {item['record_id']}",
                f"- Overall: {scores['total']}/100 ({score_label(scores['total'])})",
                f"- Theme coverage: {scores['theme']}",
                f"- Emotion coverage: {scores['emotion']}",
                f"- Keyword coverage: {scores['keywords']}",
                f"- Mode alignment: {scores['mode_alignment']}",
                f"- Structure: {scores['structure']}",
                f"- Safety: {scores['safety']}",
                "",
            ]
        )

    low_dimensions: list[str] = []
    for dimension in ("theme", "emotion", "keywords", "mode_alignment", "structure", "safety"):
        average_dimension = round(
            sum(item["scores"][dimension] for item in record_scores) / len(record_scores), 2
        )
        if average_dimension < 0.8:
            low_dimensions.append(f"{dimension}={average_dimension}")

    lines.extend(
        [
            "## Quality Read",
            f"- Low dimensions to watch: {', '.join(low_dimensions) if low_dimensions else 'none'}",
            "- If keyword coverage is low, the pipeline is not specific enough for seed scenarios.",
            "- If mode alignment is low, artist personality is bleeding across modes too much.",
            "- If safety drops, the dataset is drifting into direct imitation or blocked terms.",
            "",
        ]
    )
    return "\n".join(lines)


def default_report_path(artist_id: str) -> Path:
    return Path("reports") / f"{artist_id}_quality_report.md"


def evaluate_artist(profile_path: Path, seed_path: Path, report_path: Path | None = None) -> ArtistEvaluationSummary:
    profile = load_profile(profile_path)
    records = build_records_from_seed_file(profile_path, seed_path)
    record_scores = [score_record(profile, record) for record in records]
    report = render_report(profile, record_scores)
    final_report_path = report_path or default_report_path(profile["artist_id"])
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(report + "\n", encoding="utf-8")

    average_score = round(
        sum(item["scores"]["total"] for item in record_scores) / len(record_scores), 2
    )
    strong_records = sum(1 for item in record_scores if item["scores"]["total"] >= 90)
    return ArtistEvaluationSummary(
        report_path=final_report_path,
        total_records=len(record_scores),
        average_score=average_score,
        strong_records=strong_records,
    )
