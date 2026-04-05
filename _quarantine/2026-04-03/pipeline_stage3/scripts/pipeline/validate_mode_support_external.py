from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.mode_support_external import validate_mode_support_payload
from akira_engine.reporting import write_utf8_json, write_utf8_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate mode support curation payloads before queue merge.")
    parser.add_argument("--mode-id", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def render_report(payload: dict[str, object]) -> str:
    lines = [
        f"# Mode Support External Validation: {payload['mode_id']}",
        "",
        f"- Input dir: `{payload['input_dir']}`",
        f"- Valid: `{payload['valid_count']}`",
        f"- Invalid: `{payload['invalid_count']}`",
        "",
    ]
    for item in payload["results"]:
        lines.extend(
            [
                f"## {item['filename']}",
                f"- Valid: `{item['valid']}`",
                f"- Issues: {'; '.join(item['issues']) if item['issues'] else 'none'}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    input_dir = Path(args.input_dir).resolve()
    results = []
    for path in sorted(input_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        issues = validate_mode_support_payload(payload)
        results.append({"filename": path.name, "valid": not issues, "issues": issues})

    output = {
        "schema_version": "1.0",
        "mode_id": args.mode_id,
        "input_dir": str(input_dir),
        "valid_count": sum(1 for item in results if item["valid"]),
        "invalid_count": sum(1 for item in results if not item["valid"]),
        "results": results,
    }
    out_dir = project_root / "reports" / "quality" / "external_validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{args.mode_id}_mode_support_external_validation.json"
    md_path = out_dir / f"{args.mode_id}_mode_support_external_validation.md"
    write_utf8_json(json_path, output)
    write_utf8_text(md_path, render_report(output), trailing_newline=False)
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
