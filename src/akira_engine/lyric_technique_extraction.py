from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .training_data import load_json, write_json, write_jsonl


SOURCE_KIND_NORMALIZED = "normalized_corpus"
SOURCE_KIND_OWNED_ORIGINAL = "owned_original_hook_pilot"
VALID_SOURCE_KINDS = {SOURCE_KIND_NORMALIZED, SOURCE_KIND_OWNED_ORIGINAL}

BROKEN_CHAR_TOKENS = {"\ufffd", "占?"}
FIRST_PERSON_PATTERN = re.compile(
    r"(?:\u79c1|\u307c\u304f|\u50d5|\u4ffa|\u3042\u305f\u3057|\u3046\u3061|\u308f\u305f\u3057)"
)
SECOND_PERSON_PATTERN = re.compile(
    r"(?:\u541b|\u304d\u307f|\u3042\u306a\u305f|\u304a\u524d|\u3066\u3081\u3048)"
)


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _archive_root(project_root: Path) -> Path:
    return project_root / "_quarantine" / "2026-04-03" / "archive"


def _has_active_lyric_corpus(project_root: Path) -> bool:
    return (project_root / "lyrics").exists() and any((project_root / "lyrics").iterdir())


def _source_root(project_root: Path) -> Path:
    if _has_active_lyric_corpus(project_root):
        return project_root
    archive_root = _archive_root(project_root)
    if archive_root.exists():
        return archive_root
    return project_root


def _contains_broken_text(text: str) -> bool:
    if not text:
        return False
    return any(token in text for token in BROKEN_CHAR_TOKENS)


def _japanese_char_count(text: str) -> int:
    return len(re.findall(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]", text))


def _latin_char_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z]", text))


def _digit_char_count(text: str) -> int:
    return len(re.findall(r"[0-9]", text))


def _text_cleanliness_status(normalized_doc: dict[str, Any]) -> str:
    text = _safe_text(normalized_doc.get("normalized_text"))
    if not text:
        return "empty"
    if _contains_broken_text(text):
        return "corrupted"
    if _japanese_char_count(text) == 0:
        return "non_japanese_or_unreadable"
    return "clean"


def _lyric_source_quality(normalized_doc: dict[str, Any]) -> str:
    source_family = _safe_text(normalized_doc.get("source_family")).lower()
    if source_family == "owned_original":
        return "owned_original"
    site = _safe_text(normalized_doc.get("source_site")).lower()
    if "official" in site:
        return "official"
    if site:
        return "third_party_lyric_db"
    return "unknown"


def _ordered_sections(normalized_doc: dict[str, Any]) -> list[dict[str, Any]]:
    sections = normalized_doc.get("sections", [])
    out: list[dict[str, Any]] = []
    total = len(sections)
    for index, section in enumerate(sections):
        label = _safe_text(section.get("label")) or f"section_{index + 1}"
        lowered = label.lower()
        if "chorus" in lowered or "sabi" in lowered:
            function = "hook_release"
        elif "bridge" in lowered:
            function = "pivot"
        elif "pre" in lowered:
            function = "escalation"
        else:
            function = "setup"
        out.append(
            {
                "section_label": label,
                "normalized_role": lowered,
                "line_count": int(section.get("line_count", 0) or 0),
                "relative_position": round(index / max(1, total - 1), 3) if total > 1 else 0.0,
                "entry_energy": "medium",
                "exit_energy": "medium",
                "function": function,
            }
        )
    return out


def _all_lines(normalized_doc: dict[str, Any]) -> list[str]:
    return [
        _safe_text(line)
        for section in normalized_doc.get("sections", [])
        for line in section.get("lines", [])
        if _safe_text(line)
    ]


def _repeated_lines(normalized_doc: dict[str, Any]) -> list[str]:
    counter: Counter[str] = Counter(_all_lines(normalized_doc))
    return [line for line, count in counter.most_common() if count >= 2]


def _chorus_anchor_sections(normalized_doc: dict[str, Any]) -> list[str]:
    anchors: list[str] = []
    sections = normalized_doc.get("sections", [])
    for section in sections:
        label = _safe_text(section.get("label"))
        lowered = label.lower()
        if "chorus" in lowered or "sabi" in lowered:
            anchors.append(label)
    if anchors:
        return anchors
    if sections:
        longest = max(sections, key=lambda item: int(item.get("line_count", 0) or 0))
        return [_safe_text(longest.get("label"))]
    return []


def _hook_lines(normalized_doc: dict[str, Any]) -> list[str]:
    preset = [_safe_text(line) for line in normalized_doc.get("hook_lines", []) if _safe_text(line)]
    if preset:
        return preset[:2]
    repeated = _repeated_lines(normalized_doc)
    if repeated:
        return repeated[:2]
    anchors = set(_chorus_anchor_sections(normalized_doc))
    for section in normalized_doc.get("sections", []):
        if _safe_text(section.get("label")) in anchors:
            return [_safe_text(line) for line in section.get("lines", []) if _safe_text(line)][:2]
    return []


def _imagery_tags(normalized_doc: dict[str, Any], artist_analysis: dict[str, Any]) -> list[str]:
    text = _safe_text(normalized_doc.get("normalized_text"))
    tags: list[str] = []
    if re.search(r"[\u591c\u671d\u661f\u6708]", text):
        tags.append("night")
    if re.search(r"[\u5149\u5f71\u706f]", text):
        tags.append("light")
    if re.search(r"[\u96e8\u6fe1]", text):
        tags.append("rain")
    if re.search(r"[\u706b\u71b1]", text):
        tags.append("heat")
    if re.search(r"[\u8857\u90fd\u5e02]", text):
        tags.append("city")
    if re.search(r"[\u5fc3\u606f\u58f0\u624b\u76ee\u8840\u8108]", text):
        tags.append("body")
    if re.search(r"[\u8d70\u9032\u8e0a\u98db\u63fa]", text):
        tags.append("motion")
    if re.search(r"[\u30ce\u30a4\u30ba\u30a8\u30e9\u30fc\u30b7\u30b0\u30ca\u30eb\u30b9\u30a4\u30c3\u30c1\u30a2\u30e9\u30fc\u30e0]", text):
        tags.append("digital")
    if not tags:
        tags = [
            _safe_text(item.get("tag"))
            for item in artist_analysis.get("imagery_profile", {}).get("top_imagery_clusters", [])[:3]
            if _safe_text(item.get("tag"))
        ]
    return tags[:8]


def _motif_clusters(normalized_doc: dict[str, Any]) -> list[str]:
    text = _safe_text(normalized_doc.get("normalized_text"))
    motifs: list[str] = []
    if re.search(r"[\u5149\u5f71\u9006\u5149]", text):
        motifs.append("light_shadow")
    if re.search(r"[\u5fc3\u606f\u58f0]", text):
        motifs.append("body_voice")
    if re.search(r"[\u591c\u671d\u661f\u6708]", text):
        motifs.append("time_of_day")
    if re.search(r"[\u30ce\u30a4\u30ba\u30a8\u30e9\u30fc\u30b7\u30b0\u30ca\u30eb]", text):
        motifs.append("signal_noise")
    return motifs[:6]


def _dominant_perspective(normalized_doc: dict[str, Any]) -> str:
    text = _safe_text(normalized_doc.get("normalized_text"))
    first = len(FIRST_PERSON_PATTERN.findall(text))
    second = len(SECOND_PERSON_PATTERN.findall(text))
    if first > second and first > 0:
        return "first_person"
    if second > first and second > 0:
        return "second_person"
    return "undetermined"


def _english_insertion_level(normalized_doc: dict[str, Any]) -> str:
    text = _safe_text(normalized_doc.get("normalized_text"))
    ratio = _latin_char_count(text) / max(1, len(text))
    if ratio >= 0.08:
        return "high"
    if ratio >= 0.02:
        return "medium"
    return "low"


def _line_length_profile(normalized_doc: dict[str, Any]) -> dict[str, Any]:
    lines = _all_lines(normalized_doc)
    if not lines:
        return {"min": 0, "max": 0, "avg": 0.0}
    lengths = [len(line) for line in lines]
    return {"min": min(lengths), "max": max(lengths), "avg": round(sum(lengths) / len(lengths), 2)}


def _short_line_ratio(normalized_doc: dict[str, Any]) -> float:
    lines = _all_lines(normalized_doc)
    if not lines:
        return 0.0
    return round(sum(1 for line in lines if len(line) <= 10) / len(lines), 3)


def _terminal_sound_profile(normalized_doc: dict[str, Any]) -> dict[str, int]:
    lines = _all_lines(normalized_doc)
    counter: Counter[str] = Counter()
    for line in lines:
        counter[line[-1]] += 1
    return dict(counter.most_common(10))


def _quality_flags(normalized_doc: dict[str, Any], rights_status: str, cleanliness_status: str) -> list[str]:
    flags: list[str] = []
    text = _safe_text(normalized_doc.get("normalized_text"))
    sections = normalized_doc.get("sections", [])
    if cleanliness_status != "clean":
        flags.append(f"text:{cleanliness_status}")
    if rights_status not in {"cleared_for_training", "licensed_for_training", "internal_only_holdout"}:
        flags.append(f"rights:{rights_status}")
    if len(sections) <= 1:
        flags.append("structure:single_section")
    labels = [_safe_text(section.get("label")).lower() for section in sections if _safe_text(section.get("label"))]
    if labels and all(label.startswith("unlabeled") for label in labels):
        flags.append("structure:unlabeled_sections_only")
    if _japanese_char_count(text) == 0:
        flags.append("text:no_japanese_chars")
    if _digit_char_count(text) > _japanese_char_count(text):
        flags.append("text:digit_heavy")
    if not _hook_lines(normalized_doc):
        flags.append("hook:no_detectable_hook_lines")
    return flags


def _task_eligibility(normalized_doc: dict[str, Any], rights_status: str, cleanliness_status: str) -> dict[str, Any]:
    eligible: list[str] = []
    blocked: list[str] = []
    reasons: list[str] = []
    section_count = int(normalized_doc.get("stats", {}).get("section_count", 0) or 0)
    has_hooks = bool(_hook_lines(normalized_doc))
    if rights_status in {"cleared_for_training", "licensed_for_training"} and cleanliness_status == "clean" and has_hooks:
        eligible.append("hook_generation")
    else:
        blocked.append("hook_generation")
        reasons.append("hook_generation_requires_clean_rights_cleared_hook_lines")
    if rights_status in {"cleared_for_training", "licensed_for_training"} and cleanliness_status == "clean" and section_count >= 3:
        eligible.extend(["section_generation", "chorus_rewrite", "final_release_rewrite", "full_song_generation"])
    else:
        blocked.extend(["section_generation", "chorus_rewrite", "final_release_rewrite", "full_song_generation"])
        reasons.append("multi_section_tasks_require_clean_section_aligned_tracks")
    return {
        "eligible_tasks": sorted(set(eligible)),
        "blocked_tasks": sorted(set(blocked)),
        "blocking_reasons": sorted(set(reasons)),
    }


def build_lyric_technique_record(
    *,
    normalized_doc: dict[str, Any],
    artist_analysis: dict[str, Any],
    rights_status: str = "unknown",
) -> dict[str, Any]:
    cleanliness_status = _text_cleanliness_status(normalized_doc)
    ordered_sections = _ordered_sections(normalized_doc)
    hook_lines = _hook_lines(normalized_doc)
    imagery_tags = _imagery_tags(normalized_doc, artist_analysis)
    motif_clusters = _motif_clusters(normalized_doc)
    chorus_anchors = _chorus_anchor_sections(normalized_doc)
    dominant_arc_patterns = artist_analysis.get("emotional_profile", {}).get("dominant_arc_patterns", [])
    overall_arc_label = "undetermined"
    if dominant_arc_patterns and isinstance(dominant_arc_patterns[0], dict):
        overall_arc_label = _safe_text(dominant_arc_patterns[0].get("arc")) or "undetermined"
    return {
        "schema_version": "1.0",
        "record_type": "lyric_technique_record",
        "track_identity": {
            "track_id": _safe_text(normalized_doc.get("track_id")),
            "artist_id": _safe_text(normalized_doc.get("artist_id")),
            "title": _safe_text(normalized_doc.get("title")),
            "language": _safe_text(normalized_doc.get("language")) or "ja",
        },
        "source_integrity": {
            "rights_status": rights_status,
            "lyric_source_quality": _lyric_source_quality(normalized_doc),
            "section_alignment_status": "aligned" if ordered_sections else "missing_sections",
            "text_cleanliness_status": cleanliness_status,
        },
        "structural_blueprint": {
            "ordered_sections": ordered_sections,
            "section_count": int(normalized_doc.get("stats", {}).get("section_count", 0) or 0),
            "has_pre_chorus": any("pre" in item["normalized_role"] for item in ordered_sections),
            "has_bridge": any("bridge" in item["normalized_role"] for item in ordered_sections),
            "has_outro": any("outro" in item["normalized_role"] for item in ordered_sections),
            "chorus_anchor_sections": chorus_anchors,
            "form_confidence": "low" if cleanliness_status != "clean" else "medium",
        },
        "hook_construction": {
            "hook_lines": hook_lines,
            "hook_candidate_count": len(hook_lines),
            "hook_density": "high" if len(hook_lines) >= 2 else "low",
            "title_binding_strength": (
                "medium"
                if _safe_text(normalized_doc.get("title"))
                and any(_safe_text(normalized_doc.get("title")) in line for line in hook_lines)
                else "low"
            ),
            "repetition_profile": {"repeated_line_count": len(_repeated_lines(normalized_doc))},
            "chorus_repetition_score": round(min(1.0, len(_repeated_lines(normalized_doc)) / 4), 3),
        },
        "emotional_arc": {
            "overall_arc_label": overall_arc_label,
            "section_emotion_flow": [],
            "peak_section": chorus_anchors[0] if chorus_anchors else "",
            "release_section": chorus_anchors[-1] if chorus_anchors else "",
            "valence_trend": "undetermined",
            "intensity_trend": "undetermined",
        },
        "imagery_profile": {
            "imagery_tags": imagery_tags,
            "motif_clusters": motif_clusters,
            "object_bank": imagery_tags[:4],
            "body_reference_level": "medium" if "body" in imagery_tags else "low",
            "space_reference_level": "medium" if any(tag in imagery_tags for tag in ["city", "night", "light"]) else "low",
            "digital_reference_level": "medium" if "digital" in imagery_tags else "low",
        },
        "diction_surface": {
            "register": "mixed",
            "directness_level": "medium",
            "abstraction_level": "medium",
            "english_insertion_level": _english_insertion_level(normalized_doc),
            "slang_level": "low",
            "imperative_usage_level": "low",
        },
        "narrative_stance": {
            "dominant_perspective": _dominant_perspective(normalized_doc),
            "address_target": "undetermined",
            "narrative_distance": "medium",
            "confession_vs_performance": "undetermined",
            "irony_level": "undetermined",
        },
        "phonetic_profile": {
            "line_length_profile": _line_length_profile(normalized_doc),
            "short_line_ratio": _short_line_ratio(normalized_doc),
            "long_line_ratio": round(1.0 - _short_line_ratio(normalized_doc), 3),
            "syllabic_density_band": "unknown",
            "terminal_sound_profile": _terminal_sound_profile(normalized_doc),
            "open_vowel_release_rate": 0.0,
        },
        "contrast_devices": {
            "pivot_lines": [],
            "contrast_device_count": 0,
            "twist_presence": False,
            "contrast_device_labels": [],
        },
        "mode_evidence": {
            "candidate_modes": [
                _safe_text(item.get("mode"))
                for item in artist_analysis.get("mode_candidates", [])[:3]
                if _safe_text(item.get("mode"))
            ],
            "mode_evidence_notes": artist_analysis.get("analysis_notes", []),
            "mode_confidence": "low",
        },
        "task_eligibility": _task_eligibility(normalized_doc, rights_status, cleanliness_status),
        "quality_flags": _quality_flags(normalized_doc, rights_status, cleanliness_status),
    }


def _load_owned_original_records(project_root: Path, artists: list[str] | None) -> list[dict[str, Any]]:
    pilot_root = (
        project_root / "datasets" / "_global" / "rights_cleared_corpus_acquisition" / "owned_original_hook_pilot"
    ).resolve()
    accepted_dir = pilot_root / "accepted"
    if not accepted_dir.exists():
        return []

    records: list[dict[str, Any]] = []
    for record_path in sorted(accepted_dir.glob("*.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        artist_id = _safe_text(record.get("track_identity", {}).get("artist_id"))
        if artists and artist_id not in artists:
            continue

        lyric_ref = _safe_text(record.get("content_assets", {}).get("lyric_text_ref"))
        section_map_ref = _safe_text(record.get("content_assets", {}).get("section_map_ref"))
        if not lyric_ref or not section_map_ref:
            continue

        lyric_candidate = Path(lyric_ref)
        section_candidate = Path(section_map_ref)
        lyric_path = (
            lyric_candidate.resolve()
            if lyric_candidate.is_absolute()
            else (pilot_root / lyric_candidate).resolve()
        )
        section_map_path = (
            section_candidate.resolve()
            if section_candidate.is_absolute()
            else (pilot_root / section_candidate).resolve()
        )
        if not lyric_path.exists():
            lyric_path = (project_root / "datasets" / "_global" / "rights_cleared_corpus_acquisition" / lyric_candidate).resolve()
        if not section_map_path.exists():
            section_map_path = (project_root / "datasets" / "_global" / "rights_cleared_corpus_acquisition" / section_candidate).resolve()
        if not lyric_path.exists() or not section_map_path.exists():
            continue

        lyric_lines = [line.strip() for line in lyric_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lyric_lines and lyric_lines[0].startswith("[") and lyric_lines[0].endswith("]"):
            lyric_lines = lyric_lines[1:]
        section_map = json.loads(section_map_path.read_text(encoding="utf-8"))
        section_specs = section_map.get("sections", [])
        built_sections: list[dict[str, Any]] = []
        cursor = 0
        for index, spec in enumerate(section_specs):
            section_name = _safe_text(spec.get("section")) or f"section_{index + 1}"
            line_count = int(spec.get("line_count", 0) or 0)
            section_lines = lyric_lines[cursor : cursor + line_count] if line_count > 0 else []
            cursor += line_count
            built_sections.append(
                {
                    "label": section_name,
                    "line_count": len(section_lines),
                    "lines": section_lines,
                }
            )
        if not built_sections:
            built_sections = [
                {
                    "label": "chorus",
                    "line_count": len(lyric_lines),
                    "lines": lyric_lines,
                }
            ]

        normalized_doc = {
            "track_id": _safe_text(record.get("track_identity", {}).get("track_id")),
            "artist_id": artist_id,
            "title": _safe_text(record.get("track_identity", {}).get("title")),
            "language": "ja",
            "source_site": "owned_original",
            "source_family": "owned_original",
            "normalized_text": "\n".join(lyric_lines),
            "sections": built_sections,
            "hook_lines": [_safe_text(line) for line in section_map.get("hook_lines", []) if _safe_text(line)],
            "stats": {"section_count": len(built_sections)},
        }
        records.append(
            {
                "artist_id": artist_id,
                "normalized_doc": normalized_doc,
                "artist_analysis": {
                    "imagery_profile": {"top_imagery_clusters": []},
                    "emotional_profile": {"dominant_arc_patterns": []},
                    "mode_candidates": [],
                    "analysis_notes": [
                        "Owned-original hook pilot record imported from rights-cleared corpus acquisition workspace."
                    ],
                },
                "rights_status": _safe_text(record.get("rights_review", {}).get("rights_status")) or "unknown",
            }
        )
    return records


def extract_lyric_technique_records(
    *,
    project_root: Path,
    output_dir: Path,
    artists: list[str] | None = None,
    default_rights_status: str = "unknown",
    source_kind: str = SOURCE_KIND_NORMALIZED,
) -> dict[str, Any]:
    if source_kind not in VALID_SOURCE_KINDS:
        raise ValueError(f"Unsupported source_kind: {source_kind}")

    final_project_root = project_root.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    flagged_counts: Counter[str] = Counter()

    if source_kind == SOURCE_KIND_OWNED_ORIGINAL:
        source_root = (
            final_project_root
            / "datasets"
            / "_global"
            / "rights_cleared_corpus_acquisition"
            / "owned_original_hook_pilot"
        ).resolve()
        candidates = _load_owned_original_records(final_project_root, artists)
        if not candidates:
            skipped.append({"source_kind": source_kind, "reason": "no_owned_original_records_found"})
        for item in candidates:
            record = build_lyric_technique_record(
                normalized_doc=item["normalized_doc"],
                artist_analysis=item["artist_analysis"],
                rights_status=item["rights_status"],
            )
            for flag in record.get("quality_flags", []):
                flagged_counts[flag] += 1
            records.append(record)
    else:
        source_root = _source_root(final_project_root)
        lyrics_root = source_root / "lyrics"
        artist_dirs = [lyrics_root / artist_id for artist_id in artists] if artists else [path for path in lyrics_root.iterdir() if path.is_dir()]
        for artist_dir in artist_dirs:
            artist_id = artist_dir.name
            normalized_root = artist_dir / "normalized"
            artist_analysis_path = artist_dir / "analysis.json"
            if not normalized_root.exists() or not artist_analysis_path.exists():
                skipped.append({"artist_id": artist_id, "reason": "missing_normalized_or_artist_analysis"})
                continue
            artist_analysis = load_json(artist_analysis_path)
            for normalized_path in sorted(normalized_root.glob("*.json")):
                normalized_doc = load_json(normalized_path)
                record = build_lyric_technique_record(
                    normalized_doc=normalized_doc,
                    artist_analysis=artist_analysis,
                    rights_status=default_rights_status,
                )
                for flag in record.get("quality_flags", []):
                    flagged_counts[flag] += 1
                records.append(record)

    jsonl_path = write_jsonl(output_dir / "lyric_technique_records.jsonl", records)
    manifest = {
        "schema_version": "1.0",
        "project_root": str(final_project_root),
        "source_root": str(source_root),
        "source_kind": source_kind,
        "outputs": {"lyric_technique_records": str(jsonl_path)},
        "counts": {
            "records": len(records),
            "skipped_artifacts": len(skipped),
            "flagged_records": sum(1 for record in records if record.get("quality_flags")),
        },
        "flag_summary": dict(flagged_counts),
        "skipped_artifacts": skipped,
    }
    manifest_path = write_json(output_dir / "lyric_technique_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
