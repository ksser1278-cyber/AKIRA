from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.conditioning_merge import merge_external_conditioning_record
from akira_engine.reporting import write_utf8_json, write_utf8_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge generation_safety grounding upgrade files into reference_tracks.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--backup", action="store_true")
    return parser.parse_args()


def render_report(payload: dict[str, object]) -> str:
    lines = [
        f"# Generation Safety Grounding Conditioning Merge: {payload['artist_id']}",
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


def _validation_manifest_path(project_root: Path, artist_id: str) -> Path:
    return (
        project_root
        / "reports"
        / "quality"
        / "external_validation"
        / f"{artist_id}_generation_safety_grounding_external_validation.json"
    )


def _assert_validation_gate(project_root: Path, artist_id: str, input_dir: Path) -> None:
    manifest_path = _validation_manifest_path(project_root, artist_id)
    if not manifest_path.exists():
        raise SystemExit(f"Validation manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_input_dir = str(payload.get("input_dir", "")).strip()
    if manifest_input_dir != str(input_dir):
        raise SystemExit(
            f"Validation manifest input_dir mismatch: expected {input_dir}, found {manifest_input_dir or '<empty>'}"
        )
    if int(payload.get("invalid_count", 0)) > 0:
        raise SystemExit(f"Refusing merge: validation manifest reports invalid grounding patches in {input_dir}")


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    input_dir = Path(args.input_dir).resolve()
    target_dir = project_root / "data" / args.artist_id / "reference_tracks"
    if not target_dir.exists():
        raise SystemExit(f"Target reference_tracks directory not found: {target_dir}")
    if not input_dir.exists():
        raise SystemExit(f"Input directory not found: {input_dir}")
    _assert_validation_gate(project_root, args.artist_id, input_dir)

    backup_dir = None
    if args.backup:
        backup_dir = project_root / "reports" / "quality" / "conditioning_merge_backups" / "generation_safety_grounding" / args.artist_id

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
    manifest_path = write_utf8_json(output_dir / f"{args.artist_id}_generation_safety_grounding_conditioning_merge.json", payload)
    report_path = write_utf8_text(
        output_dir / f"{args.artist_id}_generation_safety_grounding_conditioning_merge.md",
        render_report(payload),
        trailing_newline=False,
    )
    print(manifest_path)
    print(report_path)


if __name__ == "__main__":
    main()
