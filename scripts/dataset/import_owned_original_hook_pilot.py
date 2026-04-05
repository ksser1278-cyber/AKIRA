from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse

from src.akira_engine.owned_original_training_source import import_owned_original_hook_pilot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import accepted owned-original hook pilot records into the rights map and supervised export path.",
    )
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root.")
    parser.add_argument(
        "--pilot-root",
        type=Path,
        default=Path("datasets") / "_global" / "rights_cleared_corpus_acquisition" / "owned_original_hook_pilot",
        help="Pilot workspace root.",
    )
    parser.add_argument(
        "--rights-map",
        type=Path,
        default=Path("datasets") / "_global" / "training_rights_map.json",
        help="Training rights map path to update.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets") / "training" / "owned_original_supervised",
        help="Output directory for owned-original supervised samples.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = import_owned_original_hook_pilot(
        project_root=args.project_root.resolve(),
        pilot_root=(args.project_root / args.pilot_root).resolve() if not args.pilot_root.is_absolute() else args.pilot_root.resolve(),
        rights_map_path=(args.project_root / args.rights_map).resolve() if not args.rights_map.is_absolute() else args.rights_map.resolve(),
        output_dir=(args.project_root / args.output_dir).resolve() if not args.output_dir.is_absolute() else args.output_dir.resolve(),
    )
    print(f"Import manifest: {manifest['manifest_path']}")
    print(f"Imported records: {manifest['counts']['imported_records']}")
    print(f"Samples: {manifest['counts']['samples']}")
    print(f"Skipped: {manifest['counts']['skipped']}")


if __name__ == "__main__":
    main()
