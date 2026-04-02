from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.audit import audit_corpus, render_markdown_report, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit scraped lyric corpora for training readiness.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root that contains lyrics/, artists/, and reports/.",
    )
    parser.add_argument(
        "--artists",
        help="Optional comma-separated artist_id list to audit.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("reports") / "quality" / "corpus_audit.json",
        help="Audit JSON output path.",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=Path("reports") / "quality" / "corpus_audit.md",
        help="Markdown audit report output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    artist_ids = [item.strip() for item in (args.artists or "").split(",") if item.strip()] or None

    payload = audit_corpus(project_root, artist_ids=artist_ids)

    output_json = args.output_json if args.output_json.is_absolute() else (project_root / args.output_json).resolve()
    output_report = (
        args.output_report if args.output_report.is_absolute() else (project_root / args.output_report).resolve()
    )

    write_json(output_json, payload)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(render_markdown_report(payload), encoding="utf-8")

    print(f"Audit JSON: {output_json}")
    print(f"Audit report: {output_report}")
    print(f"Artists audited: {payload['artist_count']}")
    print(f"Training-eligible tracks: {payload['total_training_eligible_tracks']}")


if __name__ == "__main__":
    main()
