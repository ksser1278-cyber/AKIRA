from __future__ import annotations

from pathlib import Path
from typing import Any

from ..demo_runtime import run_demo_songwriter


def _archive_root(project_root: Path) -> Path:
    return project_root / "_quarantine" / "2026-04-03" / "archive"


def _resolve(project_root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else (project_root / path).resolve()


def _source_root(project_root: Path) -> Path:
    archive_root = _archive_root(project_root)
    if not archive_root.exists():
        return project_root
    if (project_root / "artists").exists() and (project_root / "data").exists():
        return project_root
    return archive_root


def run_songwriter_demo(
    *,
    project_root: Path,
    artist_id: str,
    mode_id: str | None = None,
    intent: str = "",
    title_seed: str = "",
    output_dir: Path | None = None,
    candidate_count: int = 4,
    generation_mode: str = "auto",
    model_provider: str = "gpt",
    model_name: str | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    source_root = _source_root(final_project_root)
    output_root = _resolve(final_project_root, output_dir) or (final_project_root / "outputs" / "demo_songwriter").resolve()
    mode_segment = mode_id or "auto"
    final_output_dir = output_root / artist_id / mode_segment
    manifest = run_demo_songwriter(
        source_root,
        artist_id=artist_id,
        mode_id=mode_id,
        output_dir=final_output_dir,
        candidate_count=candidate_count,
        intent=intent,
        title_seed=title_seed,
        model_provider=model_provider,
        model_name=model_name,
        generation_mode=generation_mode,
    )
    manifest["source_root"] = str(source_root)
    return manifest
