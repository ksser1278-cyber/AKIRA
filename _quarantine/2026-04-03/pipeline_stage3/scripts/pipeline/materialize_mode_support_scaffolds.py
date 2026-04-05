from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.mode_support_scaffold import (
    materialize_mode_support_scaffolds,
    write_mode_support_scaffold_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize mode support drafts into canonical conditioning files.")
    parser.add_argument("--mode-id", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    input_dir = Path(args.input_dir).resolve()
    payload = materialize_mode_support_scaffolds(project_root, args.mode_id, input_dir)
    json_path, md_path = write_mode_support_scaffold_report(project_root, payload)
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
