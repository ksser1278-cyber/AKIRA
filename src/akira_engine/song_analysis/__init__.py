from __future__ import annotations

from pathlib import Path
from typing import Any


def run_song_analysis_pipeline(*, input_dir: Path, output_dir: Path | None = None) -> dict[str, Any]:
    from .pipeline import run_song_analysis_pipeline as _impl

    return _impl(input_dir=input_dir, output_dir=output_dir)


def write_song_analysis_template(*, output_dir: Path, song_id: str = "sample_song") -> dict[str, Any]:
    from .pipeline import write_song_analysis_template as _impl

    return _impl(output_dir=output_dir, song_id=song_id)


def materialize_song_analysis_inputs_from_metadata(
    *,
    metadata_dir: Path,
    output_root: Path,
    lyrics_root: Path | None = None,
    limit: int | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    from .scrape import materialize_song_analysis_inputs_from_metadata as _impl

    return _impl(
        metadata_dir=metadata_dir,
        output_root=output_root,
        lyrics_root=lyrics_root,
        limit=limit,
        overwrite=overwrite,
    )


def match_song_analysis_lyrics(
    *,
    metadata_dir: Path,
    lyrics_root: Path,
    output_root: Path,
    limit: int | None = None,
) -> dict[str, Any]:
    from .scrape import match_song_analysis_lyrics as _impl

    return _impl(
        metadata_dir=metadata_dir,
        lyrics_root=lyrics_root,
        output_root=output_root,
        limit=limit,
    )


def scrape_vocadb_song_analysis_inputs(
    *,
    project_root: Path,
    output_root: Path,
    metadata_output_dir: Path,
    page_count: int = 1,
    page_size: int = 50,
    start_offset: int = 0,
    sort: str = "PublishDate",
    materialize_limit: int | None = None,
    lyrics_root: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    from .scrape import scrape_vocadb_song_analysis_inputs as _impl

    return _impl(
        project_root=project_root,
        output_root=output_root,
        metadata_output_dir=metadata_output_dir,
        page_count=page_count,
        page_size=page_size,
        start_offset=start_offset,
        sort=sort,
        materialize_limit=materialize_limit,
        lyrics_root=lyrics_root,
        overwrite=overwrite,
    )


__all__ = [
    "run_song_analysis_pipeline",
    "write_song_analysis_template",
    "match_song_analysis_lyrics",
    "materialize_song_analysis_inputs_from_metadata",
    "scrape_vocadb_song_analysis_inputs",
]
