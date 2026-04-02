from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.akira_engine.songwriter_v2 import render_run_report, run_songwriter_v2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run representative songwriter demos from an artist representative profile.",
    )
    parser.add_argument(
        "--artist-profile",
        required=True,
        type=Path,
        help="Path to representative_demo_profile.json.",
    )
    parser.add_argument(
        "--source-jsonl",
        required=True,
        type=Path,
        help="Path to full_song_brief JSONL.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("outputs") / "songwriter_v2_representative",
        help="Root directory for representative runs.",
    )
    parser.add_argument(
        "--candidate-count",
        type=int,
        default=12,
        help="Number of candidates to generate per representative track.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    representative_profile = load_json(args.artist_profile.resolve())
    source_jsonl = args.source_jsonl.resolve()
    output_root = args.output_root if args.output_root.is_absolute() else (Path.cwd() / args.output_root).resolve()

    artist_id = str(representative_profile.get("artist_id", "artist")).strip() or "artist"
    runs: list[dict] = []

    for mode_id in representative_profile.get("mode_priority", []):
        mode_card = representative_profile.get("mode_demo_tracks", {}).get(mode_id, {})
        track_id = str(mode_card.get("track_id", "")).strip()
        if not track_id:
            continue

        run_dir = output_root / artist_id / mode_id
        manifest = run_songwriter_v2(
            source_jsonl,
            track_id=track_id,
            output_dir=run_dir,
            candidate_count=args.candidate_count,
        )
        report_path = run_dir / "run_report.md"
        report_path.write_text(render_run_report(manifest), encoding="utf-8")
        runs.append(
            {
                "mode_id": mode_id,
                "track_id": track_id,
                "title": mode_card.get("title"),
                "selected_score": manifest["selected_score"],
                "selected_lyric_path": manifest["selected_lyric_path"],
                "report_path": str(report_path),
                "manifest_path": manifest["manifest_path"],
            }
        )

    summary = {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "source_jsonl": str(source_jsonl),
        "candidate_count": args.candidate_count,
        "runs": runs,
    }
    manifest_path = output_root / artist_id / "representative_demo_manifest.json"
    write_json(manifest_path, summary)
    print(str(manifest_path))


if __name__ == "__main__":
    main()
