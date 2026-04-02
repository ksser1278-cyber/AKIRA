from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.analysis import aggregate_artist_analyses, analyze_tracks
from src.akira_engine.ingest import bootstrap_manifest, load_manifest, normalize_manifest
from src.akira_engine.profile_builder import derive_profile
from src.akira_engine.reporting import render_artist_report
from src.akira_engine.web_scrape import scrape_web_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full ingest -> analysis -> report -> draft profile pipeline for one artist."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Optional path to an existing artist lyric manifest JSON file.",
    )
    parser.add_argument(
        "--web-manifest",
        type=Path,
        help="Optional path to a web scrape manifest JSON file. If provided, scraping runs before normalization.",
    )
    parser.add_argument(
        "--artist-id",
        help="Artist ID used for auto-generating a manifest from raw lyric files.",
    )
    parser.add_argument(
        "--artist-name",
        help="Artist display name used for auto-generating a manifest from raw lyric files.",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        help="Directory of raw lyric .txt/.md files. If provided without --manifest, the manifest is auto-generated.",
    )
    parser.add_argument(
        "--manifest-out",
        type=Path,
        help="Optional output path for an auto-generated manifest. Defaults to lyrics/manifests/<artist_id>_manifest.json",
    )
    parser.add_argument(
        "--language",
        default="ja",
        help="Language code for an auto-generated manifest. Defaults to ja.",
    )
    parser.add_argument(
        "--source-type",
        default="manual_text",
        help="Source type label for an auto-generated manifest. Defaults to manual_text.",
    )
    parser.add_argument(
        "--collection-method",
        default="Manual import from user-provided lyric files for real artist analysis.",
        help="Collection method note for an auto-generated manifest.",
    )
    parser.add_argument(
        "--overwrite-web",
        action="store_true",
        help="Overwrite previously scraped raw lyric files when using --web-manifest.",
    )
    return parser.parse_args()


def validate_manifest_files(manifest_path: Path) -> str:
    manifest = load_manifest(manifest_path)
    missing_files: list[str] = []
    for track in manifest["tracks"]:
        track_path = (manifest_path.parent / track["lyric_path"]).resolve()
        if not track_path.exists():
            missing_files.append(str(track_path))
    if missing_files:
        missing = "\n".join(missing_files)
        raise SystemExit(
            "The manifest is ready, but some lyric files are missing.\n"
            f"{missing}\n"
            "Add the files and rerun the command."
        )
    return manifest["artist_id"]


def resolve_manifest_path(args: argparse.Namespace) -> Path:
    if args.web_manifest:
        summary = scrape_web_manifest(
            args.web_manifest,
            raw_output_dir=args.raw_dir,
            manifest_output_path=args.manifest_out,
            overwrite=args.overwrite_web,
        )
        print(f"Web scrape output: {summary.raw_output_dir}")
        print(f"Generated ingest manifest: {summary.manifest_path}")
        print(f"Tracks scraped: {summary.track_count}")
        return summary.manifest_path

    if args.manifest:
        return args.manifest

    missing_fields = [
        name
        for name, value in (
            ("--artist-id", args.artist_id),
            ("--artist-name", args.artist_name),
            ("--raw-dir", args.raw_dir),
        )
        if not value
    ]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise SystemExit(
            "Provide either --manifest or all of the following for auto-discovery:\n"
            f"{missing}"
        )

    manifest_path = args.manifest_out or (Path("lyrics") / "manifests" / f"{args.artist_id}_manifest.json")
    summary = bootstrap_manifest(
        artist_id=args.artist_id,
        artist_name=args.artist_name,
        raw_dir=args.raw_dir,
        manifest_path=manifest_path,
        language=args.language,
        source_type=args.source_type,
        collection_method=args.collection_method,
    )
    print(f"Auto-generated manifest: {summary.manifest_path}")
    print(f"Raw lyric files discovered: {summary.track_count}")
    return summary.manifest_path


def main() -> None:
    args = parse_args()
    manifest_path = resolve_manifest_path(args)
    artist_id = validate_manifest_files(manifest_path)

    normalized_summary = normalize_manifest(manifest_path)
    track_summaries = analyze_tracks(normalized_summary.output_dir, Path("lyrics") / "analyzed" / "tracks")
    aggregate_artist_analyses(Path("lyrics") / "analyzed" / "tracks", Path("lyrics") / "analyzed" / "artists")

    artist_analysis_path = Path("lyrics") / "analyzed" / "artists" / f"{artist_id}.json"
    report_summary = render_artist_report(
        artist_analysis_path=artist_analysis_path,
        track_analysis_root=Path("lyrics") / "analyzed" / "tracks",
    )
    profile_path = derive_profile(artist_analysis_path)

    print(f"Normalized artist dir: {normalized_summary.output_dir}")
    print(f"Track analyses written: {len(track_summaries)}")
    print(f"Artist analysis: {artist_analysis_path}")
    print(f"Style report: {report_summary.output_path}")
    print(f"Draft profile: {profile_path}")


if __name__ == "__main__":
    main()
