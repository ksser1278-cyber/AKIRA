from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
import json
from pathlib import Path

from src.akira_engine.audit import load_json, write_json
from src.akira_engine.training_data import build_training_datasets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a focused training package for one artist from the audited corpus.",
    )
    parser.add_argument(
        "--artist-id",
        required=True,
        help="artist_id to package, for example 'ado'.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root that contains reports/, datasets/, artists/, and lyrics/.",
    )
    parser.add_argument(
        "--audit-json",
        type=Path,
        default=Path("reports") / "quality" / "corpus_audit.json",
        help="Corpus audit JSON path.",
    )
    parser.add_argument(
        "--minimum-recommendation",
        choices=["needs_review", "ready"],
        default="needs_review",
        help="Minimum artist recommendation required for packaging.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional output directory. Defaults to datasets/training/<artist_id>/.",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        help="Optional markdown summary report path.",
    )
    return parser.parse_args()


def render_artist_package_report(artist_audit: dict, package_summary: dict) -> str:
    lines = [
        f"# {artist_audit['artist_id']} Training Package",
        "",
        f"- Recommendation: `{artist_audit['recommendation']}`",
        f"- Readiness score: `{artist_audit['scores']['readiness_score']}`",
        f"- Training-eligible tracks: `{artist_audit['counts']['training_eligible_tracks']}`",
        f"- Manifest tracks: `{artist_audit['counts']['manifest_tracks']}`",
        f"- Track blueprint records: `{package_summary['counts']['track_blueprints']}`",
        f"- Artist style cards: `{package_summary['counts']['artist_style_cards']}`",
        "",
        "## Main Risk Signals",
        "",
    ]

    top_issues = artist_audit.get("top_track_issue_codes", [])
    if top_issues:
        for issue in top_issues[:10]:
            lines.append(f"- `{issue['issue_code']}`: {issue['count']}")
    else:
        lines.append("- No significant track-level issues detected.")

    lines.extend(["", "## Notes", ""])
    lines.append("- This package uses derived lyric evidence, not verbatim scraped lyric targets.")
    lines.append("- The strongest current limitation is section labeling quality when source pages do not mark verse/chorus boundaries.")
    lines.append("- Rebuild this package after any normalization or analysis improvement to refresh the derived examples.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    audit_path = args.audit_json if args.audit_json.is_absolute() else (project_root / args.audit_json).resolve()
    audit_payload = load_json(audit_path)

    artist_rows = [artist for artist in audit_payload.get("artists", []) if artist.get("artist_id") == args.artist_id]
    if not artist_rows:
        raise SystemExit(f"Artist '{args.artist_id}' was not found in audit payload: {audit_path}")

    filtered_audit_payload = {
        **audit_payload,
        "artist_count": 1,
        "artists": artist_rows,
        "total_manifest_tracks": artist_rows[0]["counts"]["manifest_tracks"],
        "total_training_eligible_tracks": artist_rows[0]["counts"]["training_eligible_tracks"],
        "recommendation_counts": {artist_rows[0]["recommendation"]: 1},
    }

    output_dir = args.output_dir or (Path("datasets") / "training" / args.artist_id)
    final_output_dir = output_dir if output_dir.is_absolute() else (project_root / output_dir).resolve()
    package_summary = build_training_datasets(
        project_root,
        audit_payload=filtered_audit_payload,
        minimum_recommendation=args.minimum_recommendation,
        output_dir=final_output_dir,
    )

    filtered_audit_path = final_output_dir / f"{args.artist_id}_audit_snapshot.json"
    write_json(filtered_audit_path, filtered_audit_payload)

    report_path = args.output_report or (Path("reports") / "quality" / f"{args.artist_id}_training_package.md")
    final_report_path = report_path if report_path.is_absolute() else (project_root / report_path).resolve()
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(
        render_artist_package_report(artist_rows[0], package_summary),
        encoding="utf-8",
    )

    print(f"Artist package dir: {final_output_dir}")
    print(f"Audit snapshot: {filtered_audit_path}")
    print(f"Package report: {final_report_path}")
    print(json.dumps(package_summary["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
