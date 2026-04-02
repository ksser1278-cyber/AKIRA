from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.external_conditioning import validate_external_record
from akira_engine.reporting import write_utf8_json, write_utf8_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate producer expansion external conditioning JSON files before merge.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def render_report(payload: dict[str, object]) -> str:
    lines = [
        f"# Producer Expansion External Validation: {payload['artist_id']}",
        "",
        f"- Input dir: `{payload['input_dir']}`",
        f"- Valid: `{payload['valid_count']}`",
        f"- Invalid: `{payload['invalid_count']}`",
        "",
        "## Results",
        "",
    ]
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['filename']}",
                f"- Track id: `{item['track_id']}`",
                f"- Valid: `{item['valid']}`",
                *([f"- Issues: {'; '.join(item['issues'])}"] if item["issues"] else ["- Issues: none"]),
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    input_dir = Path(args.input_dir).resolve()
    if not input_dir.exists():
        raise SystemExit(f"Input directory not found: {input_dir}")

    results = []
    for path in sorted(input_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        issues = validate_external_record(payload)
        track_id = str(payload.get("track_identity", {}).get("track_id") or payload.get("track_id") or "").strip()
        results.append(
            {
                "filename": path.name,
                "track_id": track_id,
                "valid": not issues,
                "issues": issues,
            }
        )

    output = {
        "schema_version": "1.0",
        "artist_id": args.artist_id,
        "input_dir": str(input_dir),
        "valid_count": sum(1 for item in results if item["valid"]),
        "invalid_count": sum(1 for item in results if not item["valid"]),
        "results": results,
    }
    out_dir = project_root / "reports" / "quality" / "external_validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = write_utf8_json(out_dir / f"{args.artist_id}_producer_expansion_external_validation.json", output)
    report_path = write_utf8_text(
        out_dir / f"{args.artist_id}_producer_expansion_external_validation.md",
        render_report(output),
        trailing_newline=False,
    )
    print(manifest_path)
    print(report_path)


if __name__ == "__main__":
    main()
