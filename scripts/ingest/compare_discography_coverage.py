from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
import json
import sys
from pathlib import Path

from src.akira_engine.spotify import compare_lyric_manifest_to_spotify


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare a lyric scrape manifest against Spotify discography metadata."
    )
    parser.add_argument("--lyrics-manifest", required=True, type=Path, help="Path to lyric source manifest JSON.")
    parser.add_argument("--spotify-discography", required=True, type=Path, help="Path to Spotify discography JSON.")
    parser.add_argument("--output", type=Path, help="Optional output report markdown path.")
    return parser.parse_args()


def build_track_lines(items: list[dict], *, title_key: str, date_key: str | None = None) -> list[str]:
    if not items:
        return ["- None"]
    lines: list[str] = []
    for item in items[:50]:
        if date_key:
            lines.append(f"- {item[title_key]} ({item[date_key]})")
        else:
            lines.append(f"- {item[title_key]}")
    return lines


def build_report(payload: dict, lyrics_manifest_path: Path, spotify_path: Path) -> str:
    strict_missing = payload["spotify_missing_from_lyrics"]
    primary_missing = payload["spotify_primary_missing_from_lyrics"]
    variant_only_missing = payload["spotify_variant_only_missing_from_lyrics"]
    missing_lyrics = payload["lyric_missing_from_spotify"]

    lines = [
        "# Discography Coverage Report",
        "",
        f"- Lyrics manifest: `{lyrics_manifest_path}`",
        f"- Spotify discography: `{spotify_path}`",
        "",
        "## Summary",
        f"- Strict lyrics coverage: {payload['matched_count']} / {payload['spotify_canonical_track_count']}",
        (
            f"- Lyric-bearing works coverage: "
            f"{payload['primary_lyric_matched_count']} / {payload['spotify_primary_lyric_track_count']}"
        ),
        (
            f"- Redundant variant tracks in Spotify metadata: "
            f"{payload['spotify_redundant_variant_track_count']}"
        ),
        f"- Local lyric tracks collected: {payload['lyric_track_count']}",
        "",
        "## Primary Works Missing From Lyrics",
    ]

    lines.extend(build_track_lines(primary_missing, title_key="name", date_key="first_release_date"))
    lines.extend(["", "## Variant-Only Gaps"])
    lines.extend(build_track_lines(variant_only_missing, title_key="name", date_key="first_release_date"))
    lines.extend(["", "## Strict Spotify Missing From Lyrics"])
    lines.extend(build_track_lines(strict_missing, title_key="name", date_key="first_release_date"))
    lines.extend(["", "## Lyrics Missing From Spotify"])
    lines.extend(build_track_lines(missing_lyrics, title_key="title"))
    return "\n".join(lines) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = parse_args()
    lyrics_manifest = load_json(args.lyrics_manifest)
    spotify_discography = load_json(args.spotify_discography)
    comparison = compare_lyric_manifest_to_spotify(lyrics_manifest, spotify_discography)
    report = build_report(comparison, args.lyrics_manifest, args.spotify_discography)

    output_path = args.output or (Path("reports") / "discography" / f"{lyrics_manifest['artist_id']}_coverage.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print(f"Output: {output_path}")
    print(f"Strict coverage: {comparison['matched_count']} / {comparison['spotify_canonical_track_count']}")
    print(
        "Lyric-bearing works coverage: "
        f"{comparison['primary_lyric_matched_count']} / {comparison['spotify_primary_lyric_track_count']}"
    )
    print(f"Variant-only gaps: {len(comparison['spotify_variant_only_missing_from_lyrics'])}")
    print(f"Primary works still missing: {len(comparison['spotify_primary_missing_from_lyrics'])}")
    print(f"Lyrics missing from Spotify: {len(comparison['lyric_missing_from_spotify'])}")


if __name__ == "__main__":
    main()
