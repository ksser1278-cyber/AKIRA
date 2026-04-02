from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


MANIFEST_PATTERN = re.compile(r"(?P<artist_id>.+?)_manifest(?:\..+)?\.json$")
IGNORED_ARTIST_IDS = {
    "_template",
    "demo",
    "demo_autogen",
    "webdemo",
    "webrun",
}
BLOCKING_TRACK_ISSUES = {
    "missing_raw_file",
    "empty_raw_text",
    "too_short_text",
    "too_few_lines",
    "missing_normalized_doc",
    "malformed_normalized_doc",
    "too_few_sections",
    "missing_track_analysis",
}
TRACK_ISSUE_PENALTIES = {
    "missing_raw_file": 100,
    "empty_raw_text": 90,
    "too_short_text": 35,
    "too_few_lines": 25,
    "missing_normalized_doc": 35,
    "malformed_normalized_doc": 35,
    "too_few_sections": 15,
    "low_unique_line_ratio": 20,
    "high_unlabeled_section_ratio": 15,
    "fragmented_sections": 10,
    "high_english_insertion_ratio": 10,
    "missing_track_analysis": 20,
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def discover_artist_ids(project_root: Path) -> list[str]:
    artist_ids: set[str] = set()

    for root in [
        project_root / "lyrics" / "raw",
        project_root / "lyrics" / "normalized",
        project_root / "lyrics" / "analyzed" / "tracks",
        project_root / "artists",
    ]:
        if not root.exists():
            continue
        for path in root.iterdir():
            if path.is_dir():
                artist_ids.add(path.name)

    manifest_root = project_root / "lyrics" / "manifests"
    if manifest_root.exists():
        for path in manifest_root.glob("*_manifest*.json"):
            match = MANIFEST_PATTERN.match(path.name)
            if match:
                artist_ids.add(match.group("artist_id"))

    artist_analysis_root = project_root / "lyrics" / "analyzed" / "artists"
    if artist_analysis_root.exists():
        for path in artist_analysis_root.glob("*.json"):
            artist_ids.add(path.stem)

    return sorted(artist_id for artist_id in artist_ids if artist_id not in IGNORED_ARTIST_IDS)


def pick_manifest_path(project_root: Path, artist_id: str) -> Path | None:
    manifest_root = project_root / "lyrics" / "manifests"
    candidates = sorted(manifest_root.glob(f"{artist_id}_manifest*.json"))
    if not candidates:
        return None

    def priority(path: Path) -> tuple[int, int, str]:
        name = path.name
        try:
            payload = load_json(path)
            track_count = len(payload.get("tracks", []))
        except Exception:
            track_count = -1
        if ".merged." in name or name.endswith(".merged.json"):
            return (-track_count, 0, name)
        if name.endswith("_manifest.json"):
            return (-track_count, 1, name)
        return (-track_count, 2, name)

    return sorted(candidates, key=priority)[0]


def resolve_track_path(manifest_path: Path, lyric_path: str | None) -> Path | None:
    if not lyric_path:
        return None
    path = Path(lyric_path)
    if path.is_absolute():
        return path
    return (manifest_path.parent / path).resolve()


def normalized_path(project_root: Path, artist_id: str, track_id: str) -> Path:
    return project_root / "lyrics" / "normalized" / artist_id / f"{track_id}.json"


def track_analysis_path(project_root: Path, artist_id: str, track_id: str) -> Path:
    return project_root / "lyrics" / "analyzed" / "tracks" / artist_id / f"{track_id}.json"


def artist_analysis_path(project_root: Path, artist_id: str) -> Path:
    return project_root / "lyrics" / "analyzed" / "artists" / f"{artist_id}.json"


def generated_profile_path(project_root: Path, artist_id: str) -> Path:
    return project_root / "artists" / artist_id / "profile.generated.json"


def safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def average(values: list[float]) -> float:
    return round(mean(values), 3) if values else 0.0


def audit_track(
    project_root: Path,
    artist_id: str,
    manifest_path: Path,
    track: dict[str, Any],
) -> dict[str, Any]:
    track_id = track.get("track_id", "unknown")
    title = track.get("title", track_id)
    issues: list[str] = []

    raw_path = resolve_track_path(manifest_path, track.get("lyric_path"))
    raw_text = ""
    raw_line_count = 0
    raw_nonempty_line_count = 0
    raw_character_count = 0

    if raw_path is None or not raw_path.exists():
        issues.append("missing_raw_file")
    else:
        raw_text = safe_read_text(raw_path)
        raw_lines = raw_text.splitlines()
        raw_nonempty_lines = [line.strip() for line in raw_lines if line.strip()]
        raw_line_count = len(raw_lines)
        raw_nonempty_line_count = len(raw_nonempty_lines)
        raw_character_count = len("".join(raw_nonempty_lines))
        if not raw_nonempty_lines:
            issues.append("empty_raw_text")
        if raw_character_count and raw_character_count < 120:
            issues.append("too_short_text")
        if raw_nonempty_line_count and raw_nonempty_line_count < 6:
            issues.append("too_few_lines")

    normalized_doc_path = normalized_path(project_root, artist_id, track_id)
    normalized_doc: dict[str, Any] | None = None
    unlabeled_section_ratio = 0.0
    single_line_section_ratio = 0.0
    unique_line_ratio = 0.0
    section_count = 0
    repeated_line_count = 0

    if not normalized_doc_path.exists():
        issues.append("missing_normalized_doc")
    else:
        try:
            normalized_doc = load_json(normalized_doc_path)
            sections = normalized_doc.get("sections", [])
            stats = normalized_doc.get("stats", {})
            section_count = int(stats.get("section_count", len(sections)))
            repeated_line_count = int(stats.get("repeated_line_count", 0))
            unique_line_ratio = float(stats.get("unique_line_ratio", 0.0))
            if section_count < 3:
                issues.append("too_few_sections")
            if unique_line_ratio and unique_line_ratio < 0.45:
                issues.append("low_unique_line_ratio")
            if section_count:
                unlabeled_count = sum(1 for section in sections if str(section.get("label", "")).startswith("unlabeled"))
                single_line_count = sum(1 for section in sections if int(section.get("line_count", 0)) == 1)
                unlabeled_section_ratio = round(unlabeled_count / section_count, 3)
                single_line_section_ratio = round(single_line_count / section_count, 3)
                if section_count >= 6 and unlabeled_section_ratio > 0.85:
                    issues.append("high_unlabeled_section_ratio")
                if section_count >= 8 and single_line_section_ratio > 0.8:
                    issues.append("fragmented_sections")
        except Exception:
            issues.append("malformed_normalized_doc")

    analysis_path = track_analysis_path(project_root, artist_id, track_id)
    english_insertion_ratio = 0.0
    hook_candidate_count = 0
    if not analysis_path.exists():
        issues.append("missing_track_analysis")
    else:
        try:
            track_analysis = load_json(analysis_path)
            lexical = track_analysis.get("lexical", {})
            repetition = track_analysis.get("repetition", {})
            english_insertion_ratio = float(lexical.get("english_insertion_ratio", 0.0))
            hook_candidate_count = len(repetition.get("hook_candidates", []))
            if english_insertion_ratio > 0.45:
                issues.append("high_english_insertion_ratio")
        except Exception:
            issues.append("missing_track_analysis")

    penalty = sum(TRACK_ISSUE_PENALTIES.get(issue, 0) for issue in issues)
    score = max(0, 100 - min(penalty, 100))

    return {
        "track_id": track_id,
        "title": title,
        "score": score,
        "training_eligible": not any(issue in BLOCKING_TRACK_ISSUES for issue in issues),
        "issue_codes": sorted(set(issues)),
        "paths": {
            "raw_lyric_path": str(raw_path) if raw_path else None,
            "normalized_path": str(normalized_doc_path) if normalized_doc_path.exists() else None,
            "track_analysis_path": str(analysis_path) if analysis_path.exists() else None,
        },
        "stats": {
            "raw_line_count": raw_line_count,
            "raw_nonempty_line_count": raw_nonempty_line_count,
            "raw_character_count": raw_character_count,
            "section_count": section_count,
            "repeated_line_count": repeated_line_count,
            "unique_line_ratio": unique_line_ratio,
            "unlabeled_section_ratio": unlabeled_section_ratio,
            "single_line_section_ratio": single_line_section_ratio,
            "english_insertion_ratio": english_insertion_ratio,
            "hook_candidate_count": hook_candidate_count,
        },
    }


def safe_manifest_payload(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return None, [f"manifest_read_error:{exc}"]

    issues: list[str] = []
    if "tracks" not in payload or not isinstance(payload["tracks"], list) or not payload["tracks"]:
        issues.append("manifest_missing_tracks")
    track_ids = [track.get("track_id") for track in payload.get("tracks", []) if isinstance(track, dict)]
    duplicates = [track_id for track_id, count in Counter(track_ids).items() if track_id and count > 1]
    if duplicates:
        issues.append("manifest_duplicate_track_ids")
    return payload, issues


def audit_artist(project_root: Path, artist_id: str) -> dict[str, Any]:
    raw_dir = project_root / "lyrics" / "raw" / artist_id
    normalized_dir = project_root / "lyrics" / "normalized" / artist_id
    manifest_path = pick_manifest_path(project_root, artist_id)
    artist_analysis = artist_analysis_path(project_root, artist_id)
    generated_profile = generated_profile_path(project_root, artist_id)

    artist_issue_codes: list[str] = []
    manifest_track_count = 0
    track_details: list[dict[str, Any]] = []

    if manifest_path is None:
        artist_issue_codes.append("missing_manifest")
    else:
        manifest_payload, manifest_issues = safe_manifest_payload(manifest_path)
        artist_issue_codes.extend(manifest_issues)
        if manifest_payload and manifest_payload.get("tracks"):
            manifest_track_count = len(manifest_payload["tracks"])
            for track in manifest_payload["tracks"]:
                if isinstance(track, dict):
                    track_details.append(audit_track(project_root, artist_id, manifest_path, track))

    raw_track_count = 0
    if raw_dir.exists():
        raw_track_count = sum(1 for path in raw_dir.glob("*.txt"))
    else:
        artist_issue_codes.append("missing_raw_dir")

    normalized_track_count = 0
    if normalized_dir.exists():
        normalized_track_count = sum(1 for path in normalized_dir.glob("*.json"))

    analyzed_track_root = project_root / "lyrics" / "analyzed" / "tracks" / artist_id
    analyzed_track_count = 0
    if analyzed_track_root.exists():
        analyzed_track_count = sum(1 for path in analyzed_track_root.glob("*.json"))

    raw_coverage = min(1.0, (raw_track_count / manifest_track_count)) if manifest_track_count else 0.0
    normalized_coverage = min(1.0, (normalized_track_count / manifest_track_count)) if manifest_track_count else 0.0
    analyzed_coverage = min(1.0, (analyzed_track_count / manifest_track_count)) if manifest_track_count else 0.0
    eligible_track_count = sum(1 for detail in track_details if detail["training_eligible"])
    average_track_score = average([float(detail["score"]) for detail in track_details])
    readiness_score = round(
        (average_track_score * 0.55)
        + (raw_coverage * 100 * 0.15)
        + (normalized_coverage * 100 * 0.15)
        + (analyzed_coverage * 100 * 0.15),
        2,
    )

    if artist_analysis.exists():
        readiness_score = min(100.0, readiness_score + 2.5)
    else:
        artist_issue_codes.append("missing_artist_analysis")

    if generated_profile.exists():
        readiness_score = min(100.0, readiness_score + 2.5)
    else:
        artist_issue_codes.append("missing_generated_profile")

    track_issue_counts = Counter(issue for detail in track_details for issue in detail["issue_codes"])
    blocking_reasons = [issue for issue, _ in track_issue_counts.most_common(5)]

    if manifest_track_count == 0:
        recommendation = "blocked"
    elif readiness_score >= 75 and normalized_coverage >= 0.9 and analyzed_coverage >= 0.9:
        recommendation = "ready"
    elif readiness_score >= 50 and raw_coverage >= 0.7:
        recommendation = "needs_review"
    else:
        recommendation = "blocked"

    return {
        "artist_id": artist_id,
        "paths": {
            "manifest_path": str(manifest_path) if manifest_path else None,
            "raw_dir": str(raw_dir) if raw_dir.exists() else None,
            "normalized_dir": str(normalized_dir) if normalized_dir.exists() else None,
            "artist_analysis_path": str(artist_analysis) if artist_analysis.exists() else None,
            "generated_profile_path": str(generated_profile) if generated_profile.exists() else None,
        },
        "counts": {
            "manifest_tracks": manifest_track_count,
            "raw_tracks": raw_track_count,
            "normalized_tracks": normalized_track_count,
            "analyzed_tracks": analyzed_track_count,
            "training_eligible_tracks": eligible_track_count,
        },
        "coverage": {
            "raw_coverage": round(raw_coverage, 3),
            "normalized_coverage": round(normalized_coverage, 3),
            "analyzed_coverage": round(analyzed_coverage, 3),
        },
        "scores": {
            "average_track_score": average_track_score,
            "readiness_score": readiness_score,
        },
        "recommendation": recommendation,
        "artist_issue_codes": sorted(set(artist_issue_codes)),
        "top_track_issue_codes": [
            {"issue_code": issue, "count": count}
            for issue, count in track_issue_counts.most_common(10)
        ],
        "blocking_reasons": blocking_reasons,
        "track_details": track_details,
    }


def audit_corpus(project_root: Path, artist_ids: list[str] | None = None) -> dict[str, Any]:
    target_artist_ids = artist_ids or discover_artist_ids(project_root)
    artists = [audit_artist(project_root, artist_id) for artist_id in target_artist_ids]

    recommendation_counts = Counter(artist["recommendation"] for artist in artists)
    issue_counts = Counter(
        issue["issue_code"]
        for artist in artists
        for issue in artist["top_track_issue_codes"]
        for _ in range(issue["count"])
    )
    total_tracks = sum(artist["counts"]["manifest_tracks"] for artist in artists)
    eligible_tracks = sum(artist["counts"]["training_eligible_tracks"] for artist in artists)

    return {
        "schema_version": "1.0",
        "project_root": str(project_root),
        "artist_count": len(artists),
        "total_manifest_tracks": total_tracks,
        "total_training_eligible_tracks": eligible_tracks,
        "recommendation_counts": dict(recommendation_counts),
        "top_issue_codes": [
            {"issue_code": issue, "count": count}
            for issue, count in issue_counts.most_common(15)
        ],
        "artists": artists,
    }


def render_markdown_report(audit_payload: dict[str, Any]) -> str:
    lines = [
        "# Corpus Audit Report",
        "",
        f"- Artists audited: {audit_payload['artist_count']}",
        f"- Manifest tracks: {audit_payload['total_manifest_tracks']}",
        f"- Training-eligible tracks: {audit_payload['total_training_eligible_tracks']}",
        f"- Recommendation counts: {json.dumps(audit_payload['recommendation_counts'], ensure_ascii=False)}",
        "",
        "## Top Issue Codes",
        "",
    ]

    top_issues = audit_payload.get("top_issue_codes", [])
    if top_issues:
        for issue in top_issues[:10]:
            lines.append(f"- `{issue['issue_code']}`: {issue['count']}")
    else:
        lines.append("- No track-level issues found.")

    lines.extend(["", "## Artist Summaries", ""])
    for artist in audit_payload.get("artists", []):
        counts = artist["counts"]
        coverage = artist["coverage"]
        scores = artist["scores"]
        lines.append(f"### {artist['artist_id']}")
        lines.append(f"- Recommendation: `{artist['recommendation']}`")
        lines.append(f"- Readiness score: `{scores['readiness_score']}`")
        lines.append(
            "- Coverage: "
            f"raw `{coverage['raw_coverage']}`, "
            f"normalized `{coverage['normalized_coverage']}`, "
            f"analyzed `{coverage['analyzed_coverage']}`"
        )
        lines.append(
            "- Track counts: "
            f"manifest `{counts['manifest_tracks']}`, "
            f"raw `{counts['raw_tracks']}`, "
            f"normalized `{counts['normalized_tracks']}`, "
            f"analyzed `{counts['analyzed_tracks']}`, "
            f"eligible `{counts['training_eligible_tracks']}`"
        )
        if artist["blocking_reasons"]:
            lines.append(
                "- Main blockers: "
                + ", ".join(f"`{issue}`" for issue in artist["blocking_reasons"][:5])
            )
        if artist["artist_issue_codes"]:
            lines.append(
                "- Artist-level issues: "
                + ", ".join(f"`{issue}`" for issue in artist["artist_issue_codes"])
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
