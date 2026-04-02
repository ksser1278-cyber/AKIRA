from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.akira_engine.conditioning_style_profile import build_conditioning_style_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate validated track conditioning records into a generated artist style prompt profile.",
    )
    parser.add_argument("--artist-id", required=True, help="Artist id to aggregate.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Project root path.",
    )
    parser.add_argument(
        "--reference-root",
        type=Path,
        default=Path("data") / "reference_tracks",
        help="Root directory containing per-artist conditioning records.",
    )
    parser.add_argument(
        "--output-profile",
        type=Path,
        default=None,
        help="Explicit output profile path. Defaults to artists/<artist_id>/style_prompt_profile.generated.json",
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports") / "style_prompt_profiles",
        help="Directory where evidence reports will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    reference_root = args.reference_root if args.reference_root.is_absolute() else (project_root / args.reference_root).resolve()
    report_root = args.report_root if args.report_root.is_absolute() else (project_root / args.report_root).resolve()
    output_profile = args.output_profile
    if output_profile is None:
        output_profile = project_root / "artists" / args.artist_id / "style_prompt_profile.generated.json"
    elif not output_profile.is_absolute():
        output_profile = (project_root / output_profile).resolve()

    manifest = build_conditioning_style_profile(
        project_root=project_root,
        artist_id=args.artist_id,
        reference_root=reference_root,
        output_profile_path=output_profile,
        report_root=report_root,
    )
    print(f"Generated profile: {manifest['generated_profile_path']}")
    print(f"Report: {manifest['report_path']}")
    print(f"Mode distribution: {manifest['mode_distribution']}")
    print(f"Reference records: {manifest['reference_record_count']}")


if __name__ == "__main__":
    main()
