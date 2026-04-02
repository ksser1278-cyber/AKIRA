from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.hard_case import sync_hard_case_registry_from_manifest, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync hard-case registry from a hard-case benchmark manifest.")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--manifest-path", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    registry = sync_hard_case_registry_from_manifest(
        project_root=args.project_root,
        manifest_path=args.manifest_path.resolve(),
    )
    registry_path = args.project_root / "data" / "_global" / "hard_case_registry.json"
    write_json(registry_path, registry)
    print(registry_path)


if __name__ == "__main__":
    main()
