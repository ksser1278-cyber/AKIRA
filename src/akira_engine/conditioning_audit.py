from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HIGH_TRUST_STATUSES = {"confirmed", "cross_checked"}
LOW_TRUST_STATUSES = {"estimated", "inferred", "unknown"}


@dataclass
class RecordAudit:
    track_id: str
    title: str
    artist_id: str
    grade: str
    score: int
    blockers: list[str]
    warnings: list[str]
    metrics: dict[str, Any]
    path: str


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_statuses(obj: Any, counts: dict[str, int]) -> None:
    if isinstance(obj, dict):
        status = obj.get("status")
        if isinstance(status, str):
            counts[status] = counts.get(status, 0) + 1
        for value in obj.values():
            _count_statuses(value, counts)
        return
    if isinstance(obj, list):
        for item in obj:
            _count_statuses(item, counts)


def _count_trust_domain_statuses(record: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    trust_domains = [
        record.get("track_identity", {}),
        record.get("source_provenance", {}),
        record.get("audio_fact_layer", {}).get("reported_facts", {}),
    ]
    for domain in trust_domains:
        _count_statuses(domain, counts)
    return counts


def _has_meaningful_list(obj: dict[str, Any], key: str) -> bool:
    value = obj.get(key)
    return isinstance(value, list) and any(isinstance(item, str) and item.strip() for item in value)


def _looks_corrupted_text(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if "?" in text:
        return True
    compact = "".join(text.split())
    if not compact:
        return False
    import re

    hangul_count = len(re.findall(r"[\uac00-\ud7af]", compact))
    return hangul_count > 0


def audit_conditioning_record(path: Path) -> RecordAudit:
    record = _load_json(path)
    track_identity = record.get("track_identity", {})
    lyric_ground_truth = record.get("lyric_ground_truth", {})
    song_intent = record.get("song_intent", {})
    audio_fact_layer = record.get("audio_fact_layer", {})
    prompt_conditioning = record.get("prompt_conditioning", {})
    quality_control = record.get("quality_control", {})
    japanese_profile = record.get("japanese_lyric_profile", {})
    sections = record.get("section_analysis", [])

    counts: dict[str, int] = {}
    _count_statuses(record, counts)
    trust_counts = _count_trust_domain_statuses(record)

    full_text_status = lyric_ground_truth.get("full_text_status", "excluded")
    lyric_sections = lyric_ground_truth.get("sections", [])
    hook_lines = lyric_ground_truth.get("hook_lines", [])
    question_lines = lyric_ground_truth.get("question_lines", [])
    title_text = track_identity.get("title", "")
    section_line_samples: list[str] = []
    for section in lyric_sections[:3]:
        section_line_samples.extend(str(line).strip() for line in section.get("lines", [])[:3] if str(line or "").strip())
    corrupted_probe_texts = [title_text, *hook_lines[:3], *section_line_samples[:6]]
    corrupted_text_count = sum(1 for item in corrupted_probe_texts if _looks_corrupted_text(item))

    confirmed_count = sum(trust_counts.get(status, 0) for status in HIGH_TRUST_STATUSES)
    low_trust_count = sum(trust_counts.get(status, 0) for status in LOW_TRUST_STATUSES)
    total_status_count = confirmed_count + low_trust_count
    trusted_ratio = round((confirmed_count / total_status_count), 3) if total_status_count else 0.0

    section_count = len(sections) if isinstance(sections, list) else 0
    lyric_section_count = len(lyric_sections) if isinstance(lyric_sections, list) else 0

    prompt_anchor_count = sum(
        len(prompt_conditioning.get(key, []))
        for key in (
            "genre_anchors",
            "tempo_feels",
            "vocal_tones",
            "production_palette",
            "energy_arc",
            "imagery_anchors",
            "exclude",
        )
        if isinstance(prompt_conditioning.get(key), list)
    )

    blockers: list[str] = []
    warnings: list[str] = []
    score = 100

    if full_text_status == "excluded":
        blockers.append("lyric_ground_truth.full_text_status is excluded")
        score -= 25
    elif full_text_status == "partial":
        warnings.append("lyric text is only partial")
        score -= 12
    elif full_text_status not in {"full", "partial"}:
        blockers.append("lyric_ground_truth.full_text_status is unknown")
        score -= 20

    if lyric_section_count < 3:
        blockers.append("lyric_ground_truth.sections has fewer than 3 sections")
        score -= 15

    if corrupted_text_count >= 2:
        blockers.append("conditioning text appears corrupted or mojibake-like")
        score -= 30
    elif corrupted_text_count == 1:
        warnings.append("some conditioning text appears corrupted")
        score -= 8

    if section_count < 3:
        blockers.append("section_analysis has fewer than 3 entries")
        score -= 15

    if not hook_lines:
        blockers.append("hook_lines missing")
        score -= 12
    elif len(hook_lines) == 1:
        warnings.append("only one hook line recorded")
        score -= 3

    required_intent_keys = [
        "core_theme",
        "contrast_device",
        "dramatic_arc",
        "narrative_role",
        "title_function",
        "key_motifs",
    ]
    for key in required_intent_keys:
        value = song_intent.get(key)
        if not value:
            blockers.append(f"song_intent.{key} missing or empty")
            score -= 6

    if not _has_meaningful_list(prompt_conditioning, "imagery_anchors"):
        warnings.append("prompt_conditioning.imagery_anchors is weak")
        score -= 4

    if prompt_anchor_count < 10:
        warnings.append("prompt_conditioning is sparse")
        score -= 5

    proxy = audio_fact_layer.get("proxy_inference", {})
    if not proxy.get("confidence"):
        warnings.append("audio proxy confidence missing")
        score -= 2
    if not proxy.get("evidence_basis"):
        warnings.append("audio proxy evidence_basis missing")
        score -= 2

    if not japanese_profile:
        blockers.append("japanese_lyric_profile missing")
        score -= 10
    else:
        critic_focus = japanese_profile.get("critic_focus", [])
        if not critic_focus:
            warnings.append("japanese_lyric_profile.critic_focus missing")
            score -= 3

    missing_fields = quality_control.get("missing_fields", [])
    manual_review = quality_control.get("manual_review_required_for", [])
    if missing_fields:
        warnings.append(f"quality_control.missing_fields has {len(missing_fields)} entries")
        score -= min(10, len(missing_fields) * 2)
    if manual_review:
        warnings.append(f"manual review required for {len(manual_review)} fields")
        score -= min(10, len(manual_review) * 2)
    if not quality_control.get("ready_for_prompting", False):
        blockers.append("ready_for_prompting is false")
        score -= 20

    if trusted_ratio < 0.35:
        blockers.append("high-trust evidence ratio is too low")
        score -= 15
    elif trusted_ratio < 0.55:
        warnings.append("high-trust evidence ratio is moderate")
        score -= 5

    if not record.get("source_provenance", {}).get("lyric_sources"):
        blockers.append("lyric_sources missing")
        score -= 10
    if not record.get("source_provenance", {}).get("metadata_sources"):
        blockers.append("metadata_sources missing")
        score -= 8

    if not question_lines:
        warnings.append("question_lines missing")
        score -= 1

    score = max(0, score)
    if blockers or score < 70:
        grade = "weak"
    elif full_text_status != "full":
        grade = "usable"
    elif score < 85:
        grade = "usable"
    else:
        grade = "gold"

    metrics = {
        "trusted_ratio": trusted_ratio,
        "confirmed_or_cross_checked_claims": confirmed_count,
        "estimated_or_inferred_claims": low_trust_count,
        "lyric_section_count": lyric_section_count,
        "analysis_section_count": section_count,
        "hook_line_count": len(hook_lines),
        "question_line_count": len(question_lines),
        "prompt_anchor_count": prompt_anchor_count,
        "corrupted_text_count": corrupted_text_count,
        "missing_field_count": len(missing_fields),
        "manual_review_count": len(manual_review),
        "full_text_status": full_text_status,
    }

    return RecordAudit(
        track_id=track_identity.get("track_id", path.stem),
        title=track_identity.get("title", ""),
        artist_id=track_identity.get("artist_id", ""),
        grade=grade,
        score=score,
        blockers=blockers,
        warnings=warnings,
        metrics=metrics,
        path=str(path),
    )


def audit_artist_conditioning(artist_dir: Path) -> dict[str, Any]:
    records = []
    for path in sorted(artist_dir.glob("*.conditioning.json")):
        records.append(audit_conditioning_record(path))

    summary = {
        "artist_id": artist_dir.parent.name,
        "record_count": len(records),
        "gold_count": sum(1 for record in records if record.grade == "gold"),
        "usable_count": sum(1 for record in records if record.grade == "usable"),
        "weak_count": sum(1 for record in records if record.grade == "weak"),
        "average_score": round(sum(record.score for record in records) / len(records), 2) if records else 0.0,
        "records": [
            {
                "track_id": record.track_id,
                "title": record.title,
                "grade": record.grade,
                "score": record.score,
                "blockers": record.blockers,
                "warnings": record.warnings,
                "metrics": record.metrics,
                "path": record.path,
            }
            for record in records
        ],
    }
    return summary


def audit_conditioning_paths(paths: list[Path], artist_id: str) -> dict[str, Any]:
    records = [audit_conditioning_record(path) for path in paths]
    summary = {
        "artist_id": artist_id,
        "record_count": len(records),
        "gold_count": sum(1 for record in records if record.grade == "gold"),
        "usable_count": sum(1 for record in records if record.grade == "usable"),
        "weak_count": sum(1 for record in records if record.grade == "weak"),
        "average_score": round(sum(record.score for record in records) / len(records), 2) if records else 0.0,
        "records": [
            {
                "track_id": record.track_id,
                "title": record.title,
                "grade": record.grade,
                "score": record.score,
                "blockers": record.blockers,
                "warnings": record.warnings,
                "metrics": record.metrics,
                "path": record.path,
            }
            for record in records
        ],
    }
    return summary


def render_audit_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Conditioning Audit: {summary['artist_id']}",
        "",
        f"- Records: `{summary['record_count']}`",
        f"- Gold: `{summary['gold_count']}`",
        f"- Usable: `{summary['usable_count']}`",
        f"- Weak: `{summary['weak_count']}`",
        f"- Average score: `{summary['average_score']}`",
        "",
    ]

    for record in summary["records"]:
        lines.append(f"## {record['track_id']}")
        if record["title"]:
            lines.append(f"- Title: `{record['title']}`")
        lines.append(f"- Grade: `{record['grade']}`")
        lines.append(f"- Score: `{record['score']}`")
        lines.append(f"- Trusted ratio: `{record['metrics']['trusted_ratio']}`")
        lines.append(f"- Lyric sections: `{record['metrics']['lyric_section_count']}`")
        lines.append(f"- Analysis sections: `{record['metrics']['analysis_section_count']}`")
        lines.append(f"- Hook lines: `{record['metrics']['hook_line_count']}`")
        lines.append(f"- Prompt anchors: `{record['metrics']['prompt_anchor_count']}`")
        lines.append(f"- Corrupted text count: `{record['metrics']['corrupted_text_count']}`")
        if record["blockers"]:
            lines.append("- Blockers:")
            for blocker in record["blockers"]:
                lines.append(f"  - {blocker}")
        if record["warnings"]:
            lines.append("- Warnings:")
            for warning in record["warnings"]:
                lines.append(f"  - {warning}")
        lines.append(f"- Record: `{record['path']}`")
        lines.append("")

    return "\n".join(lines).strip() + "\n"
