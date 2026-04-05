from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse

from src.akira_engine.supervised_training_pilot import build_supervised_training_pilot_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a train/eval pilot bundle from a supervised sample JSONL export.",
    )
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root.")
    parser.add_argument(
        "--source-jsonl",
        type=Path,
        default=Path("datasets") / "training" / "owned_original_supervised" / "supervised_samples.jsonl",
        help="Supervised source JSONL.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets") / "training" / "pilots" / "owned_original_hook_v1",
        help="Pilot bundle output directory.",
    )
    parser.add_argument("--pilot-name", default="owned_original_hook_v1", help="Pilot manifest name.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_supervised_training_pilot_bundle(
        project_root=args.project_root.resolve(),
        source_jsonl=(args.project_root / args.source_jsonl).resolve() if not args.source_jsonl.is_absolute() else args.source_jsonl.resolve(),
        output_dir=(args.project_root / args.output_dir).resolve() if not args.output_dir.is_absolute() else args.output_dir.resolve(),
        pilot_name=args.pilot_name,
    )
    print(f"Pilot manifest: {manifest['manifest_path']}")
    print(f"Train: {manifest['counts']['train']}")
    print(f"Eval: {manifest['counts']['eval']}")


if __name__ == "__main__":
    main()
