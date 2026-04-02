from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.akira_engine.discography import (
    build_discography_manifest_payload,
    discover_discography_sources,
    write_web_manifest,
)
from src.akira_engine.ingest import load_manifest
from src.akira_engine.manifest_tools import merge_lyric_manifests
from src.akira_engine.spotify import compare_lyric_manifest_to_spotify, normalize_title
from src.akira_engine.web_scrape import load_web_manifest, scrape_web_manifest


NON_LYRIC_VARIANT_MARKERS = (
    "instrumental",
    "remix",
    "extended mix",
    "piano ver",
    "strings ver",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Use Spotify coverage gaps plus a secondary lyric site to build a backfill scrape manifest."
    )
    parser.add_argument("--primary-web-manifest", required=True, type=Path, help="Primary web scrape manifest path.")
    parser.add_argument("--lyrics-manifest", required=True, type=Path, help="Primary lyric source manifest path.")
    parser.add_argument("--spotify-discography", required=True, type=Path, help="Spotify discography JSON path.")
    parser.add_argument("--secondary-site", required=True, choices=["petitlyrics"], help="Secondary discovery site.")
    parser.add_argument("--secondary-artist-url", required=True, help="Secondary artist lyric page URL.")
    parser.add_argument("--output-web-manifest", type=Path, help="Output backfill web manifest path.")
    parser.add_argument("--supplemental-lyrics-manifest", type=Path, help="Output path for the supplemental lyric source manifest.")
    parser.add_argument("--merged-lyrics-manifest", type=Path, help="Merged lyric source manifest output path.")
    parser.add_argument("--scrape", action="store_true", help="Immediately scrape the matched backfill sources.")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_non_lyric_variant(title: str) -> bool:
    normalized = normalize_title(title)
    return any(marker in normalized for marker in NON_LYRIC_VARIANT_MARKERS)


def candidate_keys(title: str) -> list[str]:
    normalized = normalize_title(title)
    keys = [normalized] if normalized else []
    if " - " in title:
        base = normalize_title(title.split(" - ", 1)[0])
        if base and base not in keys:
            keys.append(base)
    return keys


def match_secondary_sources(
    missing_spotify_tracks: list[dict[str, Any]],
    secondary_sources: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    secondary_by_normalized: dict[str, list[dict[str, Any]]] = {}
    for source in secondary_sources:
        normalized = normalize_title(source["title"])
        if not normalized:
            continue
        secondary_by_normalized.setdefault(normalized, []).append(source)

    matched_sources: list[dict[str, Any]] = []
    unmatched_tracks: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for track in missing_spotify_tracks:
        if is_non_lyric_variant(track["name"]):
            unmatched_tracks.append(track)
            continue

        match_source: dict[str, Any] | None = None
        for key in candidate_keys(track["name"]):
            candidates = secondary_by_normalized.get(key, [])
            if candidates:
                match_source = candidates[0]
                break
            for normalized_source, source_list in secondary_by_normalized.items():
                if normalized_source.startswith(f"{key} ") or key.startswith(f"{normalized_source} "):
                    match_source = source_list[0]
                    break
            if match_source is not None:
                break

        if match_source is None:
            unmatched_tracks.append(track)
            continue
        if match_source["url"] in seen_urls:
            continue
        seen_urls.add(match_source["url"])
        matched_sources.append(
            {
                **match_source,
                "title": track["name"],
                "notes": (
                    f"Matched from Spotify gap '{track['name']}' using secondary source title '{match_source['title']}'."
                ),
            }
        )

    return matched_sources, unmatched_tracks


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = parse_args()

    primary_web_manifest = load_web_manifest(args.primary_web_manifest)
    lyrics_manifest = load_manifest(args.lyrics_manifest)
    spotify_discography = load_json(args.spotify_discography)
    comparison = compare_lyric_manifest_to_spotify(lyrics_manifest, spotify_discography)

    secondary_sources = discover_discography_sources(args.secondary_site, args.secondary_artist_url)
    matched_sources, unmatched_tracks = match_secondary_sources(
        comparison["spotify_missing_from_lyrics"],
        secondary_sources,
    )

    artist_id = primary_web_manifest["artist_id"]
    artist_name = primary_web_manifest["artist_name"]
    language = primary_web_manifest["language"]
    output_web_manifest = args.output_web_manifest or (
        Path("lyrics") / "web" / f"{artist_id}_spotify_backfill.{args.secondary_site}.json"
    )
    supplemental_lyrics_manifest = args.supplemental_lyrics_manifest or (
        Path("lyrics") / "manifests" / f"{artist_id}_manifest.{args.secondary_site}.json"
    )
    merged_lyrics_manifest = args.merged_lyrics_manifest or (
        Path("lyrics") / "manifests" / f"{artist_id}_manifest.merged.json"
    )

    relative_raw_dir = primary_web_manifest.get("raw_output_dir", f"../raw/{artist_id}")
    relative_lyrics_manifest = Path("..") / "manifests" / supplemental_lyrics_manifest.name
    payload = build_discography_manifest_payload(
        artist_id=artist_id,
        artist_name=artist_name,
        language=language,
        site=f"spotify_backfill_{args.secondary_site}",
        artist_url=args.secondary_artist_url,
        raw_output_dir=str(relative_raw_dir),
        manifest_output_path=str(relative_lyrics_manifest).replace("\\", "/"),
        sources=matched_sources,
    )
    write_web_manifest(output_web_manifest, payload)

    print(f"Backfill web manifest: {output_web_manifest}")
    print(f"Secondary candidate sources: {len(secondary_sources)}")
    print(f"Matched backfill sources: {len(matched_sources)}")
    print(f"Unmatched Spotify gaps after filtering: {len(unmatched_tracks)}")

    if args.scrape and matched_sources:
        summary = scrape_web_manifest(output_web_manifest, overwrite=False)
        print(f"Supplemental raw output: {summary.raw_output_dir}")
        print(f"Supplemental lyric manifest: {summary.manifest_path}")
        merged_path = merge_lyric_manifests(args.lyrics_manifest, summary.manifest_path, merged_lyrics_manifest)
        print(f"Merged lyric manifest: {merged_path}")


if __name__ == "__main__":
    main()
