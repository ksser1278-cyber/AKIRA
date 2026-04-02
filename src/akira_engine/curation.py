from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .text_quality import japanese_text_quality
from .training_data import infer_song_form


UNLABELED_PREFIX = "unlabeled_"
TITLE_PAREN_PATTERN = re.compile(r"[\(\[竊덀?.*?[\)\]?묕펹]")
TITLE_SPACE_PATTERN = re.compile(r"\s+")
TITLE_CONTEXT_SPLITTERS = (" - ", " – ", " — ", " / ")
NEUTRAL_INFERRED_LABELS = {
    "interlude",
    "outro_extension",
    "verse_1_extension",
    "single_block",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")
    return path


def clean_text(value: str) -> str:
    return " ".join(str(value).strip().split())


def title_key(title: str) -> str:
    cleaned = clean_text(title)
    cleaned = TITLE_PAREN_PATTERN.sub("", cleaned)
    cleaned = TITLE_SPACE_PATTERN.sub("", cleaned)
    return cleaned.casefold()


def title_for_quality(title: str) -> str:
    cleaned = clean_text(title)
    cleaned = TITLE_PAREN_PATTERN.sub("", cleaned).strip()
    for separator in TITLE_CONTEXT_SPLITTERS:
        if separator in cleaned:
            candidate = cleaned.split(separator, 1)[0].strip()
            if candidate:
                cleaned = candidate
                break
    return cleaned


def manifest_for_artist(project_root: Path, artist_id: str) -> Path | None:
    candidates = [
        project_root / "lyrics" / "manifests" / f"{artist_id}_manifest.merged.json",
        project_root / "lyrics" / "manifests" / f"{artist_id}_manifest.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def analysis_for_track(project_root: Path, artist_id: str, track_id: str) -> tuple[Path | None, dict[str, Any] | None]:
    path = project_root / "lyrics" / "analyzed" / "tracks" / artist_id / f"{track_id}.json"
    if not path.exists():
        return None, None
    return path, load_json(path)


def section_metrics(sections: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [clean_text(section.get("label", "")) for section in sections]
    line_counts = [len(section.get("lines", [])) for section in sections]
    labeled = [label for label in labels if label and not label.startswith(UNLABELED_PREFIX)]
    unlabeled = [label for label in labels if label.startswith(UNLABELED_PREFIX)]
    total_sections = len(sections)
    total_lines = sum(line_counts)
    return {
        "section_count": total_sections,
        "line_count": total_lines,
        "structured_section_count": len(labeled),
        "unlabeled_section_count": len(unlabeled),
        "structured_section_ratio": round(len(labeled) / max(1, total_sections), 4),
        "avg_lines_per_section": round(total_lines / max(1, total_sections), 2),
    }


def joined_lyric_text(sections: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for section in sections:
        lines.extend(clean_text(line) for line in section.get("lines", []) if clean_text(line))
    return "\n".join(lines)


def inferred_structure_summary(
    normalized_payload: dict[str, Any],
    track_analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    if not track_analysis:
        return {
            "available": False,
            "confidence": "none",
            "structure_recovered": False,
            "chorus_anchor_count": 0,
            "form_labels": [],
            "distinct_label_roots": [],
        }

    inferred = infer_song_form(normalized_payload, track_analysis)
    form_labels = [item.get("inferred_label", "") for item in inferred.get("ordered_sections", [])]
    distinct_label_roots = sorted(
        {
            label.split("_")[0]
            for label in form_labels
            if label and label not in NEUTRAL_INFERRED_LABELS
        }
    )
    chorus_anchor_count = len(inferred.get("chorus_anchor_sections", []))
    structure_recovered = (
        inferred.get("confidence") in {"medium", "high"}
        and len(form_labels) >= 4
        and chorus_anchor_count >= 1
        and len(distinct_label_roots) >= 2
    )
    return {
        "available": True,
        "confidence": inferred.get("confidence", "low"),
        "structure_recovered": structure_recovered,
        "chorus_anchor_count": chorus_anchor_count,
        "form_labels": form_labels,
        "distinct_label_roots": distinct_label_roots,
    }


def recommendation_for_record(
    *,
    title_quality: dict[str, Any],
    lyric_quality: dict[str, Any],
    section_data: dict[str, Any],
    inferred_structure: dict[str, Any],
) -> tuple[str, list[str]]:
    issues: list[str] = []
    if not title_quality.get("usable", False):
        issues.append("title_quality_low")
    if not lyric_quality.get("usable", False):
        issues.append("lyric_text_quality_low")
    if section_data["line_count"] < 12:
        issues.append("too_few_lines")
    if section_data["structured_section_ratio"] < 0.25 and not inferred_structure.get("structure_recovered", False):
        issues.append("section_labels_missing")
    if section_data["section_count"] <= 1 and not inferred_structure.get("structure_recovered", False):
        issues.append("single_block_structure")

    if "lyric_text_quality_low" in issues or "too_few_lines" in issues:
        return "reject", issues
    if "section_labels_missing" in issues or "single_block_structure" in issues or "title_quality_low" in issues:
        return "needs_review", issues
    return "ready", issues


def source_track_index(manifest_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        clean_text(track.get("track_id", "")): track
        for track in manifest_payload.get("tracks", [])
        if clean_text(track.get("track_id", ""))
    }


def curated_record(
    *,
    normalized_path: Path,
    normalized_payload: dict[str, Any],
    track_meta: dict[str, Any] | None,
    track_analysis_path: Path | None,
    track_analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    sections = list(normalized_payload.get("sections", []))
    title = clean_text(normalized_payload.get("title", "")) or clean_text((track_meta or {}).get("title", ""))
    title_core = title_for_quality(title)
    section_data = section_metrics(sections)
    lyric_quality = japanese_text_quality(joined_lyric_text(sections))
    title_quality = japanese_text_quality(title_core)
    inferred_structure = inferred_structure_summary(normalized_payload, track_analysis)
    recommendation, issues = recommendation_for_record(
        title_quality=title_quality,
        lyric_quality=lyric_quality,
        section_data=section_data,
        inferred_structure=inferred_structure,
    )

    return {
        "track_id": clean_text(normalized_payload.get("track_id", normalized_path.stem)),
        "artist_id": clean_text(normalized_payload.get("artist_id", "")),
        "title": title,
        "title_core": title_core,
        "title_key": title_key(title),
        "normalized_path": str(normalized_path),
        "raw_path": str((track_meta or {}).get("lyric_path", "")),
        "track_analysis_path": str(track_analysis_path) if track_analysis_path else "",
        "source_site": clean_text(normalized_payload.get("source_site", "") or (track_meta or {}).get("source_site", "")),
        "source_url": clean_text(normalized_payload.get("source_url", "") or (track_meta or {}).get("source_url", "")),
        "section_metrics": section_data,
        "inferred_structure": inferred_structure,
        "text_quality": {
            "title": title_quality,
            "lyrics": lyric_quality,
        },
        "recommendation": recommendation,
        "issues": issues,
    }


def duplicate_map(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(record["title_key"] for record in records if record.get("title_key"))
    return {key: count for key, count in counts.items() if count > 1}


def curate_artist(project_root: Path, artist_id: str, *, output_root: Path, report_root: Path) -> dict[str, Any]:
    normalized_dir = project_root / "lyrics" / "normalized" / artist_id
    if not normalized_dir.exists():
        raise FileNotFoundError(f"Normalized directory not found: {normalized_dir}")

    manifest_path = manifest_for_artist(project_root, artist_id)
    manifest_payload = load_json(manifest_path) if manifest_path else {"tracks": []}
    track_index = source_track_index(manifest_payload)

    records: list[dict[str, Any]] = []
    for path in sorted(normalized_dir.glob("*.json")):
        normalized_payload = load_json(path)
        track_analysis_path, track_analysis = analysis_for_track(project_root, artist_id, path.stem)
        records.append(
            curated_record(
                normalized_path=path,
                normalized_payload=normalized_payload,
                track_meta=track_index.get(path.stem),
                track_analysis_path=track_analysis_path,
                track_analysis=track_analysis,
            )
        )

    duplicates = duplicate_map(records)
    for record in records:
        duplicate_count = duplicates.get(record["title_key"], 0)
        record["duplicate_title_count"] = duplicate_count
        if duplicate_count > 1 and "duplicate_title_candidate" not in record["issues"]:
            record["issues"].append("duplicate_title_candidate")
            if record["recommendation"] == "ready":
                record["recommendation"] = "needs_review"

    recommendation_counts = Counter(record["recommendation"] for record in records)
    issue_counts = Counter(issue for record in records for issue in record["issues"])
    structure_recovery_count = sum(
        1 for record in records if record.get("inferred_structure", {}).get("structure_recovered", False)
    )

    manifest = {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "normalized_dir": str(normalized_dir),
        "manifest_path": str(manifest_path) if manifest_path else None,
        "record_count": len(records),
        "recommendation_counts": dict(recommendation_counts),
        "issue_counts": dict(issue_counts),
        "structure_recovery_count": structure_recovery_count,
    }

    out_dir = output_root / artist_id
    report_dir = report_root
    records_path = write_jsonl(out_dir / "curated_tracks.jsonl", records)
    manifest_path_out = write_json(out_dir / "curation_manifest.json", manifest)
    report_path = report_dir / f"{artist_id}_curation_report.md"
    report_path.write_text(render_curation_report(manifest, records), encoding="utf-8")

    manifest["records_path"] = str(records_path)
    manifest["curation_manifest_path"] = str(manifest_path_out)
    manifest["report_path"] = str(report_path)
    return manifest


def render_curation_report(manifest: dict[str, Any], records: list[dict[str, Any]]) -> str:
    lines = [
        f"# Curation Report: {manifest['artist_id']}",
        "",
        f"- Record count: `{manifest['record_count']}`",
        f"- Recommendations: `{manifest['recommendation_counts']}`",
        f"- Issue counts: `{manifest['issue_counts']}`",
        f"- Structure recovered from inferred form: `{manifest.get('structure_recovery_count', 0)}`",
        "",
        "## Why Raw Is Low-Value",
        "",
        "- `raw/` is a scrape transport layer, not a training-ready corpus.",
        "- file names are source IDs, not canonical track identities",
        "- section structure is often absent or only weakly preserved",
        "- even when labels are missing, the corpus needs a promotion step to recover usable song form",
        "- duplicates and alternate-source overlap can exist",
        "- raw files do not encode recommendation status or curation issues",
        "",
        "## Top Review Items",
        "",
    ]

    review_records = [record for record in records if record["recommendation"] != "ready"][:15]
    if not review_records:
        lines.append("- none")
    else:
        for record in review_records:
            lines.append(
                f"- `{record['track_id']}` / `{record['title']}`: `{record['recommendation']}` / {', '.join(record['issues'])}"
            )
    return "\n".join(lines)
