from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _modified_at(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return date.fromtimestamp(path.stat().st_mtime).isoformat()


def _latest(candidates: list[Path]) -> Path | None:
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.stat().st_mtime)


def _latest_in(root: Path, pattern: str) -> Path | None:
    if not root.exists():
        return None
    return _latest([path for path in root.rglob(pattern) if path.is_file()])


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _parse_iso_date(value: str) -> date | None:
    text = _safe_text(value)
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _issue(severity: str, code: str, message: str, source: Path | None = None) -> dict[str, Any]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "source": str(source) if source else "",
    }


def _status_level(issues: list[dict[str, Any]]) -> str:
    severities = {item["severity"] for item in issues}
    if "error" in severities:
        return "degraded"
    if "warning" in severities:
        return "attention"
    return "operational"


def _resolve_path(value: str, project_root: Path) -> Path | None:
    text = _safe_text(value)
    if not text:
        return None
    path = Path(text)
    if not path.is_absolute():
        path = (project_root / path).resolve()
    if path.exists():
        return path.resolve()
    return None


def _normalize_readiness(path: Path | None, payload: dict[str, Any]) -> dict[str, Any]:
    records = payload.get("records", [])
    counts = payload.get("counts", {})
    inputs = payload.get("inputs", {})
    generation_root = _safe_text(inputs.get("generation_root"))

    normalized = {
        "path": path,
        "generation_root": generation_root,
        "records": _as_int(counts.get("records")) or len(records),
        "joinable": _as_int(counts.get("joinable")) or sum(1 for item in records if item.get("joinable")),
        "prompt_ready": _as_int(counts.get("prompt_ready")) or sum(1 for item in records if item.get("prompt_ready")),
        "production_candidate": _as_int(counts.get("production_candidate")) or sum(1 for item in records if item.get("production_candidate")),
        "professional_target": _as_int(counts.get("professional_target")) or sum(1 for item in records if item.get("professional_target")),
        "professional_track_ids": [
            _safe_text(item.get("track_id"))
            for item in records
            if item.get("professional_target") and _safe_text(item.get("track_id"))
        ],
    }
    return normalized


def _readiness_score(item: dict[str, Any]) -> tuple[int, int, int, int, int, float]:
    path = item.get("path")
    generation_root = _safe_text(item.get("generation_root")).replace("/", "\\").lower()
    path_text = str(path).replace("/", "\\").lower() if path else ""
    trusted_generation_root = int("datasets\\training\\generation_profiles" in generation_root)
    sound_reviewed_path = int("sound_reviewed" in path_text or "sound_reviewed" in generation_root)
    professional_target = _as_int(item.get("professional_target"))
    prompt_ready = _as_int(item.get("prompt_ready"))
    records = _as_int(item.get("records"))
    modified = path.stat().st_mtime if isinstance(path, Path) and path.exists() else 0.0
    return (
        trusted_generation_root,
        sound_reviewed_path,
        professional_target,
        prompt_ready,
        records,
        modified,
    )


def _is_trusted_readiness_candidate(item: dict[str, Any]) -> bool:
    generation_root = _safe_text(item.get("generation_root")).replace("/", "\\").lower()
    path = item.get("path")
    path_text = str(path).replace("/", "\\").lower() if path else ""
    return (
        "datasets\\training\\generation_profiles" in generation_root
        or "sound_reviewed" in path_text
        or "tier1_map_seed" in path_text
    )


def _select_authoritative_readiness(
    project_root: Path,
    readiness_root: Path,
    generation_profiles_root: Path,
) -> tuple[Path | None, Path | None]:
    latest_raw_readiness_path = _latest_in(readiness_root, "generation_readiness_audit.json")
    latest_professional_cycle_path = _latest_in(generation_profiles_root, "professional_quality_cycle_manifest.json")

    preferred_paths: list[Path] = []
    if latest_professional_cycle_path:
        professional_cycle = _load_json(latest_professional_cycle_path)
        professional_readiness_path = _resolve_path(
            _safe_text(professional_cycle.get("outputs", {}).get("readiness_manifest")),
            project_root,
        )
        if professional_readiness_path:
            preferred_paths.append(professional_readiness_path)

    candidates = [path for path in readiness_root.rglob("generation_readiness_audit.json") if path.is_file()]
    normalized_candidates = [_normalize_readiness(path, _load_json(path)) for path in candidates]
    normalized_candidates.sort(key=_readiness_score, reverse=True)

    authoritative_readiness_path = preferred_paths[0] if preferred_paths else None
    if authoritative_readiness_path is None and normalized_candidates:
        authoritative_readiness_path = normalized_candidates[0]["path"]

    return authoritative_readiness_path, latest_raw_readiness_path


def build_engine_state(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    planning_root = project_root / "reports" / "planning"
    generation_profiles_root = project_root / "datasets" / "training" / "generation_profiles"
    readiness_root = planning_root / "generation_readiness_audit"
    wiki_root = project_root / "wiki" / "_meta"

    baseline_path = planning_root / "baseline_status.json"
    grounding_path = planning_root / "vocadb_lyric_grounding_status" / "vocadb_lyric_grounding_status.json"
    wiki_manifest_path = wiki_root / "akira_wiki_materialization_manifest.json"
    canonical_tier1_path = project_root / "datasets" / "_global" / "vocaloid_metadata_canonical" / "tier1_map_seed" / "canonical_manifest.json"

    latest_program_cycle_path = _latest(list(planning_root.glob("program_continuous_cycle_*.json")))
    latest_program_sweep_path = _latest(list(planning_root.glob("program_continuous_sweep_*.json")))
    latest_tier1_cycle_path = _latest_in(generation_profiles_root, "tier1_continuous_cycle_manifest.json")
    authoritative_readiness_path, latest_raw_readiness_path = _select_authoritative_readiness(
        project_root,
        readiness_root,
        generation_profiles_root,
    )

    latest_bulk_path = latest_program_cycle_path
    if latest_program_sweep_path and (
        latest_bulk_path is None or latest_program_sweep_path.stat().st_mtime > latest_bulk_path.stat().st_mtime
    ):
        latest_bulk_path = latest_program_sweep_path

    baseline = _load_json(baseline_path)
    grounding = _load_json(grounding_path)
    wiki_manifest = _load_json(wiki_manifest_path)
    canonical_tier1 = _load_json(canonical_tier1_path)
    latest_bulk = _load_json(latest_bulk_path)
    latest_tier1 = _load_json(latest_tier1_cycle_path)
    authoritative_readiness = _normalize_readiness(
        authoritative_readiness_path,
        _load_json(authoritative_readiness_path),
    )
    latest_raw_readiness = _normalize_readiness(
        latest_raw_readiness_path,
        _load_json(latest_raw_readiness_path),
    )

    issues: list[dict[str, Any]] = []

    snapshot_date = _parse_iso_date(_safe_text(baseline.get("snapshot_date")))
    if snapshot_date is not None and (date.today() - snapshot_date).days > 7:
        issues.append(
            _issue(
                "warning",
                "baseline_snapshot_old",
                f"Baseline snapshot is stale: {snapshot_date.isoformat()}",
                baseline_path,
            )
        )

    if (
        latest_raw_readiness_path
        and authoritative_readiness_path
        and latest_raw_readiness_path != authoritative_readiness_path
        and _is_trusted_readiness_candidate(latest_raw_readiness)
    ):
        issues.append(
            _issue(
                "warning",
                "latest_readiness_superseded",
                "Newest readiness audit was not selected as authoritative; a more trusted readiness source is being used.",
                latest_raw_readiness_path,
            )
        )

    wiki_inputs = wiki_manifest.get("inputs", {})
    wiki_corpus_root = _safe_text(wiki_inputs.get("canonical_corpus_root"))
    wiki_generation_root = _safe_text(wiki_inputs.get("generation_root"))
    if wiki_manifest:
        if "vocaloid_metadata_canonical" not in wiki_corpus_root or "generation_profiles" not in wiki_generation_root:
            issues.append(
                _issue(
                    "error",
                    "wiki_inputs_not_authoritative",
                    "Wiki materialization inputs do not point at canonical metadata and generation profiles.",
                    wiki_manifest_path,
                )
            )

        wiki_prompt_ready = int(wiki_manifest.get("counts", {}).get("prompt_ready_tracks", 0) or 0)
        wiki_professional = int(wiki_manifest.get("counts", {}).get("professional_target_tracks", 0) or 0)
        readiness_prompt_ready = _as_int(authoritative_readiness.get("prompt_ready"))
        readiness_professional = _as_int(authoritative_readiness.get("professional_target"))
        if wiki_prompt_ready != readiness_prompt_ready or wiki_professional != readiness_professional:
            issues.append(
                _issue(
                    "warning",
                    "wiki_readiness_mismatch",
                    (
                        "Wiki counts diverge from the latest readiness audit: "
                        f"wiki({wiki_prompt_ready}/{wiki_professional}) vs "
                        f"readiness({readiness_prompt_ready}/{readiness_professional})."
                    ),
                    wiki_manifest_path,
                )
            )

    grounding_total_accepted = int(grounding.get("counts", {}).get("total_accepted", 0) or 0)
    tier1_grounding_accepted = int(latest_tier1.get("counts", {}).get("grounding_total_accepted", 0) or 0)
    if latest_tier1 and grounding and tier1_grounding_accepted and grounding_total_accepted and tier1_grounding_accepted != grounding_total_accepted:
        issues.append(
            _issue(
                "warning",
                "grounding_count_mismatch",
                (
                    "Latest Tier1 cycle grounding count diverges from grounding status report: "
                    f"tier1({tier1_grounding_accepted}) vs grounding({grounding_total_accepted})."
                ),
                latest_tier1_cycle_path,
            )
        )

    payload = {
        "schema_version": "1.0",
        "record_type": "akira_engine_state",
        "project_root": str(project_root),
        "status_level": _status_level(issues),
        "authoritative_sources": {
            "latest_bulk_manifest": {
                "path": str(latest_bulk_path) if latest_bulk_path else "",
                "modified_at": _modified_at(latest_bulk_path),
            },
            "latest_tier1_cycle": {
                "path": str(latest_tier1_cycle_path) if latest_tier1_cycle_path else "",
                "modified_at": _modified_at(latest_tier1_cycle_path),
            },
            "authoritative_readiness_audit": {
                "path": str(authoritative_readiness_path) if authoritative_readiness_path else "",
                "modified_at": _modified_at(authoritative_readiness_path),
            },
            "latest_readiness_audit_raw": {
                "path": str(latest_raw_readiness_path) if latest_raw_readiness_path else "",
                "modified_at": _modified_at(latest_raw_readiness_path),
            },
            "grounding_status": {
                "path": str(grounding_path),
                "modified_at": _modified_at(grounding_path),
            },
            "baseline_status": {
                "path": str(baseline_path),
                "modified_at": _modified_at(baseline_path),
            },
            "wiki_manifest": {
                "path": str(wiki_manifest_path),
                "modified_at": _modified_at(wiki_manifest_path),
            },
        },
        "counts": {
            "bulk_seed_written_latest": int(latest_bulk.get("counts", {}).get("bulk_seed_written", 0) or 0),
            "bulk_canonical_records_latest": int(latest_bulk.get("counts", {}).get("bulk_canonical_records", 0) or 0),
            "bulk_core_latest": int(latest_bulk.get("counts", {}).get("bulk_core", 0) or 0),
            "bulk_low_value_retained_latest": int(latest_bulk.get("counts", {}).get("bulk_low_value_retained", 0) or 0),
            "tier1_canonical_records": int(canonical_tier1.get("counts", {}).get("accepted_records", 0) or 0),
            "grounding_total_incoming": int(grounding.get("counts", {}).get("total_incoming", 0) or 0),
            "grounding_total_accepted": grounding_total_accepted,
            "grounding_total_needs_patch": int(grounding.get("counts", {}).get("total_needs_patch", 0) or 0),
            "readiness_records": _as_int(authoritative_readiness.get("records")),
            "readiness_joinable": _as_int(authoritative_readiness.get("joinable")),
            "readiness_prompt_ready": _as_int(authoritative_readiness.get("prompt_ready")),
            "readiness_production_candidate": _as_int(authoritative_readiness.get("production_candidate")),
            "readiness_professional_target": _as_int(authoritative_readiness.get("professional_target")),
            "tier1_active_valid": int(latest_tier1.get("counts", {}).get("pilot20_valid", 0) or 0),
            "tier1_active_invalid": int(latest_tier1.get("counts", {}).get("pilot20_invalid", 0) or 0),
            "tier1_active_overlap": int(latest_tier1.get("counts", {}).get("pilot20_overlap", 0) or 0),
            "tier1_professional_target": int(latest_tier1.get("counts", {}).get("pilot10_professional_target", 0) or 0),
            "wiki_track_pages": int(wiki_manifest.get("counts", {}).get("track_pages", 0) or 0),
            "wiki_prompt_ready_tracks": int(wiki_manifest.get("counts", {}).get("prompt_ready_tracks", 0) or 0),
            "wiki_professional_target_tracks": int(wiki_manifest.get("counts", {}).get("professional_target_tracks", 0) or 0),
        },
        "professional_target_tracks": authoritative_readiness.get("professional_track_ids", []),
        "stale_or_conflicting_state": issues,
    }
    return payload


def render_engine_state_markdown(payload: dict[str, Any]) -> str:
    counts = payload.get("counts", {})
    sources = payload.get("authoritative_sources", {})
    issues = payload.get("stale_or_conflicting_state", [])
    professional_track_ids = payload.get("professional_target_tracks", [])

    issue_lines = [
        f"- `{item['severity']}` `{item['code']}`: {item['message']}"
        for item in issues
    ] or ["- none"]

    return "\n".join(
        [
            "# AKIRA Engine State",
            "",
            f"- status level: `{_safe_text(payload.get('status_level'))}`",
            f"- tier1 canonical: `{counts.get('tier1_canonical_records', 0)}`",
            f"- grounding accepted: `{counts.get('grounding_total_accepted', 0)}`",
            f"- grounding needs patch: `{counts.get('grounding_total_needs_patch', 0)}`",
            f"- readiness prompt-ready: `{counts.get('readiness_prompt_ready', 0)}`",
            f"- readiness professional-target: `{counts.get('readiness_professional_target', 0)}`",
            f"- active tier1 overlap: `{counts.get('tier1_active_overlap', 0)}`",
            f"- latest bulk canonical batch: `{counts.get('bulk_canonical_records_latest', 0)}`",
            "",
            "## Authoritative Sources",
            "",
            f"- latest bulk manifest: `{_safe_text(sources.get('latest_bulk_manifest', {}).get('path'))}`",
            f"- latest tier1 cycle: `{_safe_text(sources.get('latest_tier1_cycle', {}).get('path'))}`",
            f"- authoritative readiness audit: `{_safe_text(sources.get('authoritative_readiness_audit', {}).get('path'))}`",
            f"- latest readiness audit raw: `{_safe_text(sources.get('latest_readiness_audit_raw', {}).get('path'))}`",
            f"- grounding status: `{_safe_text(sources.get('grounding_status', {}).get('path'))}`",
            f"- baseline status: `{_safe_text(sources.get('baseline_status', {}).get('path'))}`",
            f"- wiki manifest: `{_safe_text(sources.get('wiki_manifest', {}).get('path'))}`",
            "",
            "## Stale Or Conflicting State",
            "",
            *issue_lines,
            "",
            "## Professional Target Tracks",
            "",
            *([f"- `{track_id}`" for track_id in professional_track_ids] or ["- none"]),
        ]
    )
