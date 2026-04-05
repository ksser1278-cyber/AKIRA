from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse

from src.akira_engine.lyric_technique_extraction import extract_lyric_technique_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract lyric technique records from normalized lyric corpora.")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root.")
    parser.add_argument("--output-dir", type=Path, default=Path("datasets") / "training" / "technique", help="Technique-record output directory.")
    parser.add_argument("--artists", nargs="*", help="Optional artist ids to limit extraction.")
    parser.add_argument("--default-rights-status", default="unknown")
    parser.add_argument("--source-kind", choices=["normalized_corpus", "owned_original_hook_pilot"], default="normalized_corpus")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = extract_lyric_technique_records(
        project_root=args.project_root.resolve(),
        output_dir=(args.project_root / args.output_dir).resolve() if not args.output_dir.is_absolute() else args.output_dir.resolve(),
        artists=args.artists,
        default_rights_status=args.default_rights_status,
        source_kind=args.source_kind,
    )
    print(f"Technique manifest: {manifest['manifest_path']}")
    print(f"Records: {manifest['counts']['records']}")
    print(f"Source root: {manifest['source_root']}")


if __name__ == "__main__":
    main()
