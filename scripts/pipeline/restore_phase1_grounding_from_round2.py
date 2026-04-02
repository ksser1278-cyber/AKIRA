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
    parser = argparse.ArgumentParser(description="Restore contaminated phase1 grounding records from round2 incoming copies.")
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def load_phase1_tracks(project_root: Path) -> list[tuple[str, str]]:
    overview_path = (
        project_root
        / "data"
        / "_global"
        / "generation_safety_grounding_upgrade"
        / "phase1_core_cleanup"
        / "overview.json"
    )
    overview = json.loads(overview_path.read_text(encoding="utf-8"))
    tracks: list[tuple[str, str]] = []
    for artist in overview.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        for track in artist.get("tracks", []):
            track_id = str(track.get("track_id", "")).strip()
            if artist_id and track_id:
                tracks.append((artist_id, track_id))
    return tracks


def render_report(payload: dict[str, object]) -> str:
    lines = [
        "# Phase 1 Grounding Restore From Round2",
        "",
        f"- restored `{payload['restored_count']}`",
        f"- missing source `{payload['missing_source_count']}`",
        "",
        "## Results",
        "",
    ]
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['track_id']}",
                f"- artist: `{item['artist_id']}`",
                f"- source: `{item['source_path']}`",
                f"- target: `{item['target_path']}`",
                f"- restored: `{item['restored']}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    backup_root = (
        project_root
        / "reports"
        / "quality"
        / "conditioning_merge_backups"
        / "generation_safety_grounding_phase1_restore"
    )

    results: list[dict[str, object]] = []
    for artist_id, track_id in load_phase1_tracks(project_root):
        source_path = (
            project_root
            / "data"
            / "_global"
            / "round2_expansion"
            / artist_id
            / "incoming"
            / f"{track_id}.json"
        )
        target_dir = project_root / "data" / artist_id / "reference_tracks"
        if not source_path.exists():
            results.append(
                {
                    "artist_id": artist_id,
                    "track_id": track_id,
                    "source_path": str(source_path),
                    "target_path": str(target_dir),
                    "restored": False,
                    "missing_source": True,
                }
            )
            continue

        merge_result = merge_external_conditioning_record(
            artist_id=artist_id,
            target_dir=target_dir,
            source_path=source_path,
            backup_dir=backup_root / artist_id,
        )
        results.append(
            {
                "artist_id": artist_id,
                "track_id": track_id,
                "source_path": str(source_path),
                "target_path": merge_result.target_path,
                "restored": merge_result.changed,
                "missing_source": False,
            }
        )

    payload = {
        "schema_version": "1.0",
        "record_type": "phase1_grounding_restore_from_round2",
        "restored_count": sum(1 for item in results if item["restored"]),
        "missing_source_count": sum(1 for item in results if item["missing_source"]),
        "results": results,
    }

    output_dir = project_root / "reports" / "quality" / "conditioning_merge"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "phase1_grounding_restore_from_round2.json"
    md_path = output_dir / "phase1_grounding_restore_from_round2.md"
    write_utf8_json(json_path, payload)
    write_utf8_text(md_path, render_report(payload), trailing_newline=False)
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
