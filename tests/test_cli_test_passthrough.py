from __future__ import annotations

from pathlib import Path

from src.akira_engine.cli.app import build_parser


def test_cli_test_command_accepts_pytest_options() -> None:
    parser = build_parser(Path("C:/tmp/akira"))

    args, unknown = parser.parse_known_args(["test", "-q"])

    args.pytest_args.extend(unknown)

    assert args.pytest_args == ["-q"]


def test_cli_test_command_captures_optional_separator() -> None:
    parser = build_parser(Path("C:/tmp/akira"))

    args = parser.parse_args(["test", "--", "-q"])

    assert args.pytest_args == ["--", "-q"]


def test_cli_has_song_analysis_run_command() -> None:
    parser = build_parser(Path("C:/tmp/akira"))

    args = parser.parse_args(["song-analysis", "run", "--input-dir", "C:/tmp/input"])

    assert str(args.input_dir) == "C:\\tmp\\input" or str(args.input_dir) == "C:/tmp/input"


def test_cli_has_song_analysis_scrape_vocadb_command() -> None:
    parser = build_parser(Path("C:/tmp/akira"))

    args = parser.parse_args(
        [
            "song-analysis",
            "scrape-vocadb",
            "--metadata-output-dir",
            "C:/tmp/meta",
            "--output-root",
            "C:/tmp/packages",
            "--page-count",
            "2",
            "--page-size",
            "5",
        ]
    )

    assert args.page_count == 2
    assert args.page_size == 5


def test_cli_has_song_analysis_materialize_metadata_command() -> None:
    parser = build_parser(Path("C:/tmp/akira"))

    args = parser.parse_args(
        [
            "song-analysis",
            "materialize-metadata",
            "--metadata-dir",
            "C:/tmp/meta",
            "--output-root",
            "C:/tmp/packages",
            "--limit",
            "3",
        ]
    )

    assert args.limit == 3


def test_cli_has_song_analysis_match_lyrics_command() -> None:
    parser = build_parser(Path("C:/tmp/akira"))

    args = parser.parse_args(
        [
            "song-analysis",
            "match-lyrics",
            "--metadata-dir",
            "C:/tmp/meta",
            "--lyrics-root",
            "C:/tmp/lyrics",
            "--output-root",
            "C:/tmp/match",
        ]
    )

    assert args.metadata_dir.name == "meta"
    assert args.lyrics_root.name == "lyrics"
