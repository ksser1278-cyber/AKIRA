from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.reporting import write_utf8_json, write_utf8_text

TRUSTED_STATUSES = {"confirmed", "cross_checked"}
SUPPORTED_MODE_IDS = {"ironic_meta", "direct_emotional_pop", "dark_cute_breakdown"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generation_safety promotion JSON files before merge.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def _trusted_source_count(items: object) -> int:
    if not isinstance(items, list):
        return 0
    return sum(
        1
        for item in items
        if isinstance(item, dict)
        and str(item.get("status", "")).strip() in TRUSTED_STATUSES
    )


def validate_promotion_record(payload: dict[str, object]) -> list[str]:
    issues: list[str] = []
    track_identity = payload.get("track_identity", {})
    if not isinstance(track_identity, dict):
        track_identity = {}
    track_id = str(track_identity.get("track_id") or payload.get("track_id") or "").strip()
    if not track_id:
        issues.append("track_id missing")

    source_provenance = payload.get("source_provenance", {})
    if not isinstance(source_provenance, dict):
        source_provenance = {}
    lyric_sources = source_provenance.get("lyric_sources", [])
    metadata_sources = source_provenance.get("metadata_sources", [])
    if _trusted_source_count(lyric_sources) == 0:
        issues.append("trusted lyric_sources missing")
    if _trusted_source_count(metadata_sources) == 0:
        issues.append("trusted metadata_sources missing")

    song_intent = payload.get("song_intent", {})
    if not isinstance(song_intent, dict):
        song_intent = {}
    narrative_role = song_intent.get("narrative_role", [])
    if not isinstance(narrative_role, list):
        issues.append("song_intent.narrative_role must be a list")
    else:
        declared_modes = [
            str(item).strip()
            for item in narrative_role
            if str(item).strip() in SUPPORTED_MODE_IDS
        ]
        if len(declared_modes) != 1:
            issues.append("song_intent.narrative_role must declare exactly one supported mode")

    return issues


def render_report(payload: dict[str, object]) -> str:
    lines = [
        f"# Generation Safety Promotion External Validation: {payload['artist_id']}",
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
        issues = validate_promotion_record(payload)
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
    manifest_path = write_utf8_json(out_dir / f"{args.artist_id}_generation_safety_promotion_external_validation.json", output)
    report_path = write_utf8_text(
        out_dir / f"{args.artist_id}_generation_safety_promotion_external_validation.md",
        render_report(output),
        trailing_newline=False,
    )
    print(manifest_path)
    print(report_path)


if __name__ == "__main__":
    main()
