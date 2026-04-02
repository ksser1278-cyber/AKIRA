from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
import sys
from pathlib import Path

from src.akira_engine.discography import discover_discography_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover all lyric page URLs from a supported artist discography page and generate a web scrape manifest."
    )
    parser.add_argument("--artist-id", required=True, help="Stable artist ID used in local outputs.")
    parser.add_argument("--artist-name", required=True, help="Artist display name.")
    parser.add_argument("--site", required=True, choices=["utaten"], help="Discovery source site.")
    parser.add_argument("--artist-url", required=True, help="Artist lyric/discography page URL.")
    parser.add_argument("--output", type=Path, help="Output web manifest path.")
    parser.add_argument("--language", default="ja", help="Language code. Defaults to ja.")
    parser.add_argument(
        "--raw-output-dir",
        default=None,
        help="Raw lyric output dir stored inside the generated web manifest. Defaults to lyrics/raw/<artist_id>.",
    )
    parser.add_argument(
        "--manifest-output-path",
        default=None,
        help="Ingest manifest path stored inside the generated web manifest. Defaults to lyrics/manifests/<artist_id>_manifest.json.",
    )
    parser.add_argument(
        "--request-delay-seconds",
        type=float,
        default=0.0,
        help="Optional delay between discovery page requests and downstream scrape requests stored in the manifest.",
    )
    return parser.parse_args()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = parse_args()
    output_path = args.output or (Path("lyrics") / "web" / f"{args.artist_id}_discography.{args.site}.json")
    raw_output_dir = args.raw_output_dir or f"../raw/{args.artist_id}"
    manifest_output_path = args.manifest_output_path or f"../manifests/{args.artist_id}_manifest.json"

    summary = discover_discography_manifest(
        artist_id=args.artist_id,
        artist_name=args.artist_name,
        language=args.language,
        site=args.site,
        artist_url=args.artist_url,
        output_path=output_path,
        raw_output_dir=raw_output_dir,
        manifest_output_path=manifest_output_path,
        request_delay_seconds=args.request_delay_seconds,
    )
    print(f"Discography manifest: {summary.output_path}")
    print(f"Discovery site: {summary.site}")
    print(f"Artist page: {summary.source_url}")
    print(f"Tracks discovered: {summary.track_count}")


if __name__ == "__main__":
    main()
