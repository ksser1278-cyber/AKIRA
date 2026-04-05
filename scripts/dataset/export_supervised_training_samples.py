from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse

from src.akira_engine.cli import run_export_supervised_samples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export supervised training samples from AKIRA derived track-blueprint records.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root.",
    )
    parser.add_argument(
        "--derived-jsonl",
        type=Path,
        default=Path("datasets") / "training" / "track_blueprints.jsonl",
        help="Derived track blueprint JSONL.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets") / "training" / "supervised",
        help="Output directory for supervised samples.",
    )
    parser.add_argument(
        "--rights-map",
        type=Path,
        help="Optional JSON mapping of track_id to rights_status.",
    )
    parser.add_argument(
        "--include-eval-only",
        action="store_true",
        help="Allow internal_only_holdout records into the export as eval/test-style samples.",
    )
    parser.add_argument(
        "--include-full-song",
        action="store_true",
        help="Also export full_song_generation samples. Default is hook_generation only.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = run_export_supervised_samples(
        project_root=args.project_root.resolve(),
        derived_jsonl=args.derived_jsonl,
        output_dir=args.output_dir,
        rights_map=args.rights_map,
        include_eval_only=args.include_eval_only,
        include_full_song=args.include_full_song,
    )

    print(f"Supervised manifest: {manifest['manifest_path']}")
    print(f"Samples: {manifest['counts']['samples']}")
    print(f"Skipped: {manifest['counts']['skipped']}")


if __name__ == "__main__":
    main()
