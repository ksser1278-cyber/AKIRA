from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
import sys
from pathlib import Path

from src.akira_engine.spotify import (
    SpotifyClient,
    build_artist_discography_snapshot,
    choose_best_artist_match,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch official artist discography metadata from Spotify and save it as JSON."
    )
    parser.add_argument("--artist-name", required=True, help="Artist name used for Spotify search.")
    parser.add_argument("--spotify-artist-id", help="Optional explicit Spotify artist ID.")
    parser.add_argument("--output", type=Path, help="Output JSON path.")
    parser.add_argument("--market", default="JP", help="Spotify market. Defaults to JP.")
    parser.add_argument(
        "--include-groups",
        default="album,single,compilation",
        help="Spotify album groups. Defaults to album,single,compilation.",
    )
    return parser.parse_args()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = parse_args()
    client = SpotifyClient.from_env()

    if args.spotify_artist_id:
        artist_id = args.spotify_artist_id
    else:
        matches = client.search_artist(args.artist_name)
        match = choose_best_artist_match(matches, args.artist_name)
        artist_id = match.artist_id
        print(f"Spotify artist: {match.name} ({match.artist_id})")

    snapshot = build_artist_discography_snapshot(
        client=client,
        artist_id=artist_id,
        market=args.market,
        include_groups=args.include_groups,
    )
    artist_slug = snapshot["artist"]["name"].lower().replace(" ", "_")
    output_path = args.output or (Path("data") / "spotify" / f"{artist_slug}_discography.json")
    write_json(output_path, snapshot)

    print(f"Output: {output_path}")
    print(f"Releases: {snapshot['release_count']}")
    print(f"Canonical tracks: {snapshot['canonical_track_count']}")
    print(f"Raw release tracks: {snapshot['raw_track_total']}")


if __name__ == "__main__":
    main()
