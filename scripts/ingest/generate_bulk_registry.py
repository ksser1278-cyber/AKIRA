from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.akira_engine.discography import discover_discography_sources
from src.akira_engine.web_scrape import DEFAULT_USER_AGENT


UTATEN_SEARCH_URL = "https://utaten.com/search"


@dataclass
class ResolvedArtist:
    artist_id: str
    artist_name: str
    search_query: str
    utaten_artist_url: str
    discovered_track_count: int


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a bulk artist registry by resolving UtaTen artist lyric pages from candidate names."
    )
    parser.add_argument("--candidates", required=True, type=Path, help="Path to the artist candidate JSON file.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("lyrics") / "bulk" / "artist_registry.generated.json",
        help="Output bulk registry JSON path.",
    )
    parser.add_argument(
        "--resolution-report",
        type=Path,
        default=Path("lyrics") / "bulk" / "artist_resolution.generated.json",
        help="Output resolution report JSON path.",
    )
    parser.add_argument(
        "--minimum-track-count",
        type=int,
        default=5,
        help="Only include artists whose discovered UtaTen page exposes at least this many tracks.",
    )
    parser.add_argument(
        "--max-artists",
        type=int,
        default=100,
        help="Maximum number of resolved artists to keep in the generated registry.",
    )
    parser.add_argument(
        "--request-delay-seconds",
        type=float,
        default=0.2,
        help="Per-page delay to store in the generated bulk registry.",
    )
    parser.add_argument(
        "--artist-delay-seconds",
        type=float,
        default=0.5,
        help="Per-artist delay to store in the generated bulk registry.",
    )
    return parser.parse_args()


def resolve_utaten_artist_url(search_query: str, session: requests.Session) -> str | None:
    response = session.get(UTATEN_SEARCH_URL, params={"artist_name": search_query}, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    lyric_link = soup.select_one("p.searchResult__title a[href^='/lyric/']")
    if lyric_link is None:
        return None

    lyric_url = urljoin(response.url, lyric_link.get("href", ""))
    lyric_response = session.get(lyric_url, timeout=20)
    lyric_response.raise_for_status()
    lyric_soup = BeautifulSoup(lyric_response.text, "html.parser")
    artist_link = lyric_soup.select_one("a[href^='/artist/lyric/']")
    if artist_link is None:
        return None
    return urljoin(lyric_response.url, artist_link.get("href", ""))


def build_registry_payload(
    resolved_artists: list[ResolvedArtist],
    *,
    request_delay_seconds: float,
    artist_delay_seconds: float,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "defaults": {
            "language": "ja",
            "spotify_market": "JP",
            "spotify_include_groups": "album,single,compilation",
            "request_delay_seconds": request_delay_seconds,
            "artist_delay_seconds": artist_delay_seconds,
        },
        "artists": [
            {
                "artist_id": item.artist_id,
                "artist_name": item.artist_name,
                "enabled": True,
                "primary_discovery": {
                    "site": "utaten",
                    "artist_url": item.utaten_artist_url,
                },
                "spotify_artist_name": item.artist_name,
                **(
                    {"manual_backfill_manifest": "lyrics/web/ado_manual_backfill.utaten.json"}
                    if item.artist_id == "ado"
                    else {}
                ),
            }
            for item in resolved_artists
        ],
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = parse_args()
    candidates = load_json(args.candidates)
    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_USER_AGENT})

    resolved: list[ResolvedArtist] = []
    unresolved: list[dict[str, Any]] = []

    for candidate in candidates["artists"]:
        utaten_url: str | None = None
        used_query: str | None = None
        failure_reasons: list[str] = []

        for query in candidate.get("search_queries", [candidate["artist_name"]]):
            try:
                resolved_url = resolve_utaten_artist_url(query, session)
                if not resolved_url:
                    failure_reasons.append(f"{query}: no artist link")
                    continue
                sources = discover_discography_sources("utaten", resolved_url)
                if len(sources) < args.minimum_track_count:
                    failure_reasons.append(f"{query}: only {len(sources)} tracks")
                    continue
                utaten_url = resolved_url
                used_query = query
                resolved.append(
                    ResolvedArtist(
                        artist_id=candidate["artist_id"],
                        artist_name=candidate["artist_name"],
                        search_query=query,
                        utaten_artist_url=resolved_url,
                        discovered_track_count=len(sources),
                    )
                )
                print(f"resolved {candidate['artist_name']} -> {resolved_url} ({len(sources)} tracks)")
                break
            except Exception as exc:  # pragma: no cover - CLI helper
                failure_reasons.append(f"{query}: {exc}")

        if utaten_url is None:
            unresolved.append(
                {
                    "artist_id": candidate["artist_id"],
                    "artist_name": candidate["artist_name"],
                    "search_queries": candidate.get("search_queries", [candidate["artist_name"]]),
                    "failures": failure_reasons,
                }
            )

        if len(resolved) >= args.max_artists:
            break

    registry_payload = build_registry_payload(
        resolved,
        request_delay_seconds=args.request_delay_seconds,
        artist_delay_seconds=args.artist_delay_seconds,
    )
    resolution_payload = {
        "schema_version": "1.0",
        "minimum_track_count": args.minimum_track_count,
        "resolved_count": len(resolved),
        "unresolved_count": len(unresolved),
        "resolved": [item.__dict__ for item in resolved],
        "unresolved": unresolved,
    }

    write_json(args.output, registry_payload)
    write_json(args.resolution_report, resolution_payload)
    print(f"Registry: {args.output}")
    print(f"Resolution report: {args.resolution_report}")
    print(f"Resolved artists: {len(resolved)}")
    print(f"Unresolved artists: {len(unresolved)}")


if __name__ == "__main__":
    main()
