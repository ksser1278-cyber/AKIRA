from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.mode_support_audit import build_mode_support_audit, write_mode_support_audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit mode support conditioning records.")
    parser.add_argument("--mode-id", required=True)
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    summary = build_mode_support_audit(project_root, args.mode_id)
    json_path, md_path = write_mode_support_audit(project_root, args.mode_id, summary)
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
