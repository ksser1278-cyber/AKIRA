from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.external_conditioning import build_external_handoff_payload
from akira_engine.reporting import write_utf8_json, write_utf8_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build external enrichment handoff manifests for producer expansion tracks.")
    parser.add_argument("--artist-id", required=True, help="Artist or producer id")
    parser.add_argument("--project-root", default=".", help="Project root path")
    return parser.parse_args()


def render_report(payload: dict[str, object]) -> str:
    lines = [
        f"# Producer Expansion Handoff: {payload['artist_id']}",
        "",
        f"- Queue source: `{payload['queue_filename']}`",
        f"- Target dir: `{payload['target_dir']}`",
        f"- Track count: `{payload['track_count']}`",
        "",
        "## Tracks",
        "",
    ]
    for item in payload["tracks"]:
        lines.extend(
            [
                f"### {item['track_id']}",
                f"- Target: `{item['target_path']}`",
                f"- Current full_text_status: `{item['full_text_status']}`",
                f"- ready_for_prompting: `{item['current_grade_hint']}`",
                f"- External work: {', '.join(item['required_external_work'])}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    payload = build_external_handoff_payload(
        project_root,
        args.artist_id,
        queue_filename="expansion_queue.json",
        required_external_work=[
            "full_lyric_grounding",
            "section_analysis_expansion",
            "source_provenance_strengthening",
            "prompt_conditioning_completion",
            "audio_enrichment_if_available",
        ],
    )
    output_dir = project_root / "data" / "_global" / "external_handoff" / args.artist_id / "producer_expansion"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = write_utf8_json(output_dir / "handoff_manifest.json", payload)
    report_path = write_utf8_text(output_dir / "handoff_manifest.md", render_report(payload), trailing_newline=False)
    inbox_dir = output_dir / "incoming"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    print(manifest_path)
    print(report_path)
    print(inbox_dir)


if __name__ == "__main__":
    main()
