from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .akira_wiki_materializer import materialize_akira_wiki
from .baseline_status import build_baseline_status, render_baseline_status_markdown
from .engine_state import build_engine_state, render_engine_state_markdown
from .reporting import write_utf8_json, write_utf8_text


def _archive_root(project_root: Path) -> Path:
    return project_root / "_quarantine" / "2026-04-03" / "archive"


def _source_root(project_root: Path) -> Path:
    archive_root = _archive_root(project_root)
    if not archive_root.exists():
        return project_root
    if (project_root / "artists").exists() and (project_root / "data").exists():
        return project_root
    return archive_root


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_path(value: Any, project_root: Path) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text)
    if not path.is_absolute():
        path = (project_root / path).resolve()
    return path.resolve() if path.exists() else None


def sync_engine_surface(
    *,
    project_root: Path,
    wiki_root: Path | None = None,
    report_root: Path | None = None,
    data_root: Path | None = None,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    final_wiki_root = (wiki_root or (project_root / "wiki")).resolve()
    final_report_root = (report_root or (project_root / "reports" / "planning")).resolve()
    final_data_root = (data_root or (project_root / "data")).resolve()
    final_wiki_root.mkdir(parents=True, exist_ok=True)
    final_report_root.mkdir(parents=True, exist_ok=True)
    final_data_root.mkdir(parents=True, exist_ok=True)

    source_root = _source_root(project_root)
    baseline_payload = build_baseline_status(source_root)
    baseline_data_path = final_data_root / "baseline_registry.json"
    baseline_json_path = final_report_root / "baseline_status.json"
    baseline_md_path = final_report_root / "baseline_status.md"
    write_utf8_json(baseline_data_path, baseline_payload)
    write_utf8_json(baseline_json_path, baseline_payload)
    write_utf8_text(baseline_md_path, render_baseline_status_markdown(baseline_payload))

    state_before = build_engine_state(project_root)
    authoritative_sources = state_before.get("authoritative_sources", {})
    readiness_path = _resolve_path(authoritative_sources.get("authoritative_readiness_audit", {}).get("path"), project_root)
    tier1_cycle_path = _resolve_path(authoritative_sources.get("latest_tier1_cycle", {}).get("path"), project_root)

    wiki_manifest_path = ""
    if readiness_path is not None and tier1_cycle_path is not None:
        readiness_manifest = _load_json(readiness_path)
        tier1_cycle_manifest = _load_json(tier1_cycle_path)
        canonical_corpus_root = _resolve_path(tier1_cycle_manifest.get("inputs", {}).get("corpus_root"), project_root)
        generation_root = _resolve_path(readiness_manifest.get("inputs", {}).get("generation_root"), project_root)
        if canonical_corpus_root is not None and generation_root is not None:
            wiki_manifest = materialize_akira_wiki(
                canonical_corpus_root=canonical_corpus_root,
                generation_root=generation_root,
                readiness_manifest_path=readiness_path,
                output_root=final_wiki_root,
            )
            wiki_manifest_path = str(wiki_manifest["manifest_path"])

    state_after = build_engine_state(project_root)
    engine_state_json_path = final_report_root / "engine_state.json"
    engine_state_md_path = final_report_root / "engine_state.md"
    write_utf8_json(engine_state_json_path, state_after)
    write_utf8_text(engine_state_md_path, render_engine_state_markdown(state_after))

    manifest = {
        "schema_version": "1.0",
        "record_type": "engine_surface_sync_manifest",
        "project_root": str(project_root),
        "status_level_before": state_before.get("status_level", "unknown"),
        "status_level_after": state_after.get("status_level", "unknown"),
        "counts": {
            "readiness_prompt_ready": int(state_after.get("counts", {}).get("readiness_prompt_ready", 0) or 0),
            "readiness_professional_target": int(state_after.get("counts", {}).get("readiness_professional_target", 0) or 0),
            "wiki_track_pages": int(state_after.get("counts", {}).get("wiki_track_pages", 0) or 0),
        },
        "outputs": {
            "baseline_data_path": str(baseline_data_path),
            "baseline_json_path": str(baseline_json_path),
            "baseline_md_path": str(baseline_md_path),
            "wiki_manifest_path": wiki_manifest_path,
            "engine_state_json_path": str(engine_state_json_path),
            "engine_state_md_path": str(engine_state_md_path),
        },
    }
    manifest_path = final_report_root / "engine_surface_sync.json"
    write_utf8_json(manifest_path, manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
