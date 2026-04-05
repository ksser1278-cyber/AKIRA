from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse

from src.akira_engine.vertex_supervised_export import export_vertex_supervised_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export an AKIRA supervised pilot bundle into Vertex AI supervised tuning JSONL files.",
    )
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root.")
    parser.add_argument(
        "--train-jsonl",
        type=Path,
        default=Path("datasets") / "training" / "pilots" / "owned_original_hook_v1" / "train.jsonl",
        help="AKIRA train JSONL.",
    )
    parser.add_argument(
        "--eval-jsonl",
        type=Path,
        default=Path("datasets") / "training" / "pilots" / "owned_original_hook_v1" / "eval.jsonl",
        help="AKIRA eval JSONL.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets") / "training" / "vertex" / "owned_original_hook_v1",
        help="Vertex-format export output directory.",
    )
    parser.add_argument("--base-model", default="gemini-2.5-flash")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = export_vertex_supervised_jsonl(
        project_root=args.project_root.resolve(),
        train_jsonl=(args.project_root / args.train_jsonl).resolve() if not args.train_jsonl.is_absolute() else args.train_jsonl.resolve(),
        eval_jsonl=(args.project_root / args.eval_jsonl).resolve() if not args.eval_jsonl.is_absolute() else args.eval_jsonl.resolve(),
        output_dir=(args.project_root / args.output_dir).resolve() if not args.output_dir.is_absolute() else args.output_dir.resolve(),
        base_model=args.base_model,
    )
    print(f"Vertex export manifest: {manifest['manifest_path']}")
    print(f"Train samples: {manifest['counts']['train_samples']}")
    print(f"Eval samples: {manifest['counts']['eval_samples']}")


if __name__ == "__main__":
    main()
