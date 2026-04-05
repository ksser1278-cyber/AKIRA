from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.conditioning_merge import merge_external_conditioning_record
from akira_engine.reporting import write_utf8_json, write_utf8_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge generation_safety promotion files into reference_tracks.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--backup", action="store_true")
    return parser.parse_args()


def render_report(payload: dict[str, object]) -> str:
    lines = [
        f"# Generation Safety Promotion Conditioning Merge: {payload['artist_id']}",
        "",
        f"- Input dir: `{payload['input_dir']}`",
        f"- Merged files: `{payload['merged_count']}`",
        f"- Unchanged files: `{payload['unchanged_count']}`",
        "",
        "## Results",
        "",
    ]
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['track_id']}",
                f"- Changed: `{item['changed']}`",
                f"- Source: `{item['source_path']}`",
                f"- Target: `{item['target_path']}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    input_dir = Path(args.input_dir).resolve()
    target_dir = project_root / "data" / args.artist_id / "reference_tracks"
    if not target_dir.exists():
        raise SystemExit(f"Target reference_tracks directory not found: {target_dir}")
    if not input_dir.exists():
        raise SystemExit(f"Input directory not found: {input_dir}")

    backup_dir = None
    if args.backup:
        backup_dir = project_root / "reports" / "quality" / "conditioning_merge_backups" / "generation_safety_promotion" / args.artist_id

    results = []
    for path in sorted(input_dir.glob("*.json")):
        results.append(
            merge_external_conditioning_record(
                artist_id=args.artist_id,
                target_dir=target_dir,
                source_path=path,
                backup_dir=backup_dir,
            )
        )

    payload = {
        "schema_version": "1.0",
        "artist_id": args.artist_id,
        "input_dir": str(input_dir),
        "merged_count": sum(1 for item in results if item.changed),
        "unchanged_count": sum(1 for item in results if not item.changed),
        "results": [
            {
                "track_id": item.track_id,
                "target_path": item.target_path,
                "source_path": item.source_path,
                "changed": item.changed,
            }
            for item in results
        ],
    }

    output_dir = project_root / "reports" / "quality" / "conditioning_merge"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = write_utf8_json(output_dir / f"{args.artist_id}_generation_safety_promotion_conditioning_merge.json", payload)
    report_path = write_utf8_text(
        output_dir / f"{args.artist_id}_generation_safety_promotion_conditioning_merge.md",
        render_report(payload),
        trailing_newline=False,
    )
    print(manifest_path)
    print(report_path)


if __name__ == "__main__":
    main()
