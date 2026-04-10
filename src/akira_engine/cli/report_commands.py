from __future__ import annotations

from pathlib import Path
from typing import Any

from ..baseline_status import build_baseline_status, render_baseline_status_markdown
from ..engine_state import build_engine_state, render_engine_state_markdown
from ..engine_health import build_engine_health, render_engine_health_markdown
from ..reporting import write_utf8_json, write_utf8_text


def _archive_root(project_root: Path) -> Path:
    return project_root / "_quarantine" / "2026-04-03" / "archive"


def _source_root(project_root: Path) -> Path:
    archive_root = _archive_root(project_root)
    if not archive_root.exists():
        return project_root
    if (project_root / "artists").exists() and (project_root / "data").exists():
        return project_root
    return archive_root


def run_report_engine_health(
    *,
    project_root: Path,
    artists: list[str],
    output_dir: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    source_root = _source_root(final_project_root)
    final_output_dir = (
        output_dir.resolve()
        if output_dir and output_dir.is_absolute()
        else (final_project_root / (output_dir or Path("reports") / "health")).resolve()
    )
    final_output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_engine_health(artists, project_root_path=source_root)
    json_path = final_output_dir / "engine_health.json"
    md_path = final_output_dir / "engine_health.md"
    write_utf8_json(json_path, payload)
    write_utf8_text(md_path, render_engine_health_markdown(payload), trailing_newline=False)
    return {
        "json_path": str(json_path),
        "md_path": str(md_path),
        "source_root": str(source_root),
    }


def run_report_baseline(
    *,
    project_root: Path,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    source_root = _source_root(final_project_root)
    final_output_root = (
        output_root.resolve()
        if output_root and output_root.is_absolute()
        else final_project_root
    )
    data_dir = final_output_root / "data"
    report_dir = final_output_root / "reports" / "planning"
    data_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = build_baseline_status(source_root)
    data_path = data_dir / "baseline_registry.json"
    json_path = report_dir / "baseline_status.json"
    md_path = report_dir / "baseline_status.md"
    write_utf8_json(data_path, payload)
    write_utf8_json(json_path, payload)
    write_utf8_text(md_path, render_baseline_status_markdown(payload))
    return {
        "data_path": str(data_path),
        "json_path": str(json_path),
        "md_path": str(md_path),
        "source_root": str(source_root),
    }


def run_report_engine_state(
    *,
    project_root: Path,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_output_root = (
        output_root.resolve()
        if output_root and output_root.is_absolute()
        else final_project_root
    )
    report_dir = final_output_root / "reports" / "planning"
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = build_engine_state(final_project_root)
    json_path = report_dir / "engine_state.json"
    md_path = report_dir / "engine_state.md"
    write_utf8_json(json_path, payload)
    write_utf8_text(md_path, render_engine_state_markdown(payload))
    return {
        "json_path": str(json_path),
        "md_path": str(md_path),
        "status_level": payload.get("status_level", "unknown"),
    }
