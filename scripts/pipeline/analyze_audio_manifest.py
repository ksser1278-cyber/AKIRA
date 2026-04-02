from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.audio_analysis import analyze_manifest, load_audio_manifest, render_audio_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze owned audio files listed in audio_manifest.json")
    parser.add_argument("--manifest", default="data/audio_manifest.json", help="Path to audio manifest")
    parser.add_argument("--project-root", default=".", help="Project root")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    manifest_path = (project_root / args.manifest).resolve() if not Path(args.manifest).is_absolute() else Path(args.manifest)

    manifest = load_audio_manifest(manifest_path)
    summary = analyze_manifest(manifest)

    output_dir = project_root / "reports" / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "audio_analysis_summary.json"
    md_path = output_dir / "audio_analysis_summary.md"

    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_audio_markdown(summary), encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
