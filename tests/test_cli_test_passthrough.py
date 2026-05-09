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
