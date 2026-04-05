from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.generation_safety import SUPPORT_ARTISTS, infer_generation_safety, load_json
from akira_engine.reporting import write_utf8_json, write_utf8_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generation_safety grounding upgrade JSON files before merge.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def _deep_merge(base: object, patch: object) -> object:
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = {**base}
        for key, value in patch.items():
            merged[key] = _deep_merge(base.get(key), value) if key in base else deepcopy(value)
        return merged
    if isinstance(base, list) and isinstance(patch, list):
        return deepcopy(patch)
    return deepcopy(patch)


def _track_path(project_root: Path, artist_id: str, track_id: str) -> Path:
    prefix = f"{artist_id}_"
    suffix = track_id[len(prefix) :] if track_id.startswith(prefix) else track_id
    return project_root / "data" / artist_id / "reference_tracks" / f"{suffix}.conditioning.json"


def _audit_lookup(project_root: Path, artist_id: str, track_id: str) -> dict[str, object] | None:
    audit_path = project_root / "reports" / "quality" / "conditioning" / f"{artist_id}_conditioning_audit_active.json"
    if not audit_path.exists():
        return None
    payload = load_json(audit_path)
    for record in payload.get("records", []):
        if str(record.get("track_id", "")).strip() == track_id:
            return {
                "grade": str(record.get("grade", "")).strip(),
                "score": float(record.get("score", 0.0)),
            }
    return None


def validate_grounding_record(project_root: Path, artist_id: str, payload: dict[str, object]) -> tuple[list[str], dict[str, object] | None]:
    track_identity = payload.get("track_identity", {})
    if not isinstance(track_identity, dict):
        track_identity = {}
    track_id = str(track_identity.get("track_id") or payload.get("track_id") or "").strip()
    if not track_id:
        return ["track_id missing"], None

    target_path = _track_path(project_root, artist_id, track_id)
    if not target_path.exists():
        return [f"target record not found: {target_path}"], None

    current = load_json(target_path)
    merged = _deep_merge(current, payload)
    audit_meta = _audit_lookup(project_root, artist_id, track_id)
    verdict = infer_generation_safety(merged, audit_meta)
    issues: list[str] = []
    if verdict.get("verdict") not in {"planner_safe", "generation_safe", "benchmark_safe"}:
        issues.append(f"merged verdict remains {verdict.get('verdict')}")
    if verdict.get("blockers"):
        issues.extend([f"blocker:{blocker}" for blocker in verdict.get("blockers", [])])
    return issues, verdict


def render_report(payload: dict[str, object]) -> str:
    lines = [
        f"# Generation Safety Grounding External Validation: {payload['artist_id']}",
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
                f"- Post-merge verdict: `{item['post_merge_verdict']}`",
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
        issues, verdict = validate_grounding_record(project_root, args.artist_id, payload)
        track_id = str(payload.get("track_identity", {}).get("track_id") or payload.get("track_id") or "").strip()
        results.append(
            {
                "filename": path.name,
                "track_id": track_id,
                "valid": not issues,
                "issues": issues,
                "post_merge_verdict": str((verdict or {}).get("verdict", "")),
                "post_merge_score": float((verdict or {}).get("score", 0.0)),
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
    manifest_path = write_utf8_json(out_dir / f"{args.artist_id}_generation_safety_grounding_external_validation.json", output)
    report_path = write_utf8_text(
        out_dir / f"{args.artist_id}_generation_safety_grounding_external_validation.md",
        render_report(output),
        trailing_newline=False,
    )
    print(manifest_path)
    print(report_path)
    if output["invalid_count"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
