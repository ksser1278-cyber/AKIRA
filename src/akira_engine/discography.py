from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.akira_engine.web_scrape import (
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_USER_AGENT,
    build_requests_session,
    is_allowed_by_robots,
    parse_html,
)


UTATEN_DISCOVERY_SELECTOR = "p.searchResult__title a[href^='/lyric/']"
PETITLYRICS_ROW_SELECTOR = "table#lyrics_list tr"
PETITLYRICS_PAGE_PATTERN = re.compile(r"/lyrics/artist/(?P<artist_id>\d+)/(?P<page>\d+)-1\.html")
SUPPORTED_DISCOVERY_SITES = {"petitlyrics", "utaten"}


@dataclass
class DiscographyDiscoverySummary:
    output_path: Path
    site: str
    source_url: str
    track_count: int


def normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def utaten_track_id_from_url(source_url: str) -> str:
    match = re.search(r"/lyric/([^/]+)/?$", source_url)
    if not match:
        raise ValueError(f"Could not infer a UtaTen track ID from URL: {source_url}")
    return f"utaten_{match.group(1)}"


def petitlyrics_track_id_from_url(source_url: str) -> str:
    match = re.search(r"/lyrics/(\d+)/?$", source_url)
    if not match:
        raise ValueError(f"Could not infer a PetitLyrics track ID from URL: {source_url}")
    return f"petitlyrics_{match.group(1)}"


def discover_utaten_sources(artist_url: str, soup: BeautifulSoup) -> list[dict[str, Any]]:
    seen_urls: set[str] = set()
    sources: list[dict[str, Any]] = []

    for link in soup.select(UTATEN_DISCOVERY_SELECTOR):
        href = link.get("href", "").strip()
        title = normalize_title(link.get_text(" ", strip=True))
        if not href or not title:
            continue

        source_url = urljoin(artist_url, href)
        if source_url in seen_urls:
            continue
        seen_urls.add(source_url)

        sources.append(
            {
                "url": source_url,
                "track_id": utaten_track_id_from_url(source_url),
                "title": title,
                "site_preset": "utaten",
                "extraction_mode": "auto",
            }
        )

    if not sources:
        raise ValueError("No UtaTen lyric links were discovered from the artist page.")
    return sources


def petitlyrics_artist_id_from_url(artist_url: str) -> str:
    match = re.search(r"/lyrics/artist/(\d+)", artist_url)
    if not match:
        raise ValueError(f"Could not infer a PetitLyrics artist ID from URL: {artist_url}")
    return match.group(1)


def petitlyrics_total_pages(artist_url: str, soup: BeautifulSoup) -> int:
    artist_id = petitlyrics_artist_id_from_url(artist_url)
    page_numbers = {1}
    for link in soup.select(f'a[href*="/lyrics/artist/{artist_id}/"]'):
        href = link.get("href", "")
        match = PETITLYRICS_PAGE_PATTERN.search(href)
        if match:
            page_numbers.add(int(match.group("page")))
    return max(page_numbers)


def petitlyrics_page_url(artist_url: str, page_number: int) -> str:
    if page_number <= 1:
        return artist_url
    base = artist_url.rstrip("/")
    return f"{base}/{page_number}-1.html"


def discover_petitlyrics_page_sources(page_url: str, soup: BeautifulSoup) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for row in soup.select(PETITLYRICS_ROW_SELECTOR):
        cells = row.select("td")
        if len(cells) < 2:
            continue
        link = cells[1].select_one('a[href^="/lyrics/"]')
        if link is None:
            continue
        href = link.get("href", "").strip()
        title = normalize_title(link.get_text(" ", strip=True))
        if not href or not title:
            continue
        if not re.fullmatch(r"/lyrics/\d+", href):
            continue

        source_url = urljoin(page_url, href)
        sources.append(
            {
                "url": source_url,
                "track_id": petitlyrics_track_id_from_url(source_url),
                "title": title,
                "site_preset": "petitlyrics",
                "extraction_mode": "auto",
            }
        )
    return sources


def discover_petitlyrics_sources(
    artist_url: str,
    soup: BeautifulSoup,
    *,
    request_delay_seconds: float = 0.0,
) -> list[dict[str, Any]]:
    total_pages = petitlyrics_total_pages(artist_url, soup)
    session = build_requests_session(DEFAULT_USER_AGENT)
    seen_urls: set[str] = set()
    sources: list[dict[str, Any]] = []

    for page_number in range(1, total_pages + 1):
        page_url = petitlyrics_page_url(artist_url, page_number)
        if page_number > 1 and request_delay_seconds > 0:
            time.sleep(request_delay_seconds)
        page_soup = soup if page_number == 1 else parse_html(
            session.get(page_url, timeout=DEFAULT_TIMEOUT_SECONDS).text
        )
        for source in discover_petitlyrics_page_sources(page_url, page_soup):
            if source["url"] in seen_urls:
                continue
            seen_urls.add(source["url"])
            sources.append(source)

    if not sources:
        raise ValueError("No PetitLyrics lyric links were discovered from the artist page.")
    return sources


def discover_discography_sources(
    site: str,
    artist_url: str,
    *,
    request_delay_seconds: float = 0.0,
) -> list[dict[str, Any]]:
    if site not in SUPPORTED_DISCOVERY_SITES:
        supported = ", ".join(sorted(SUPPORTED_DISCOVERY_SITES))
        raise ValueError(f"Unsupported discovery site '{site}'. Supported sites: {supported}")

    if not is_allowed_by_robots(artist_url, DEFAULT_USER_AGENT):
        raise SystemExit(f"Blocked by robots.txt: {artist_url}")

    session = build_requests_session(DEFAULT_USER_AGENT)
    response = session.get(artist_url, timeout=DEFAULT_TIMEOUT_SECONDS)
    response.raise_for_status()
    soup = parse_html(response.text)

    if site == "utaten":
        return discover_utaten_sources(artist_url, soup)
    if site == "petitlyrics":
        return discover_petitlyrics_sources(
            artist_url,
            soup,
            request_delay_seconds=request_delay_seconds,
        )
    raise ValueError(f"Unsupported discovery site '{site}'.")


def write_web_manifest(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def build_discography_manifest_payload(
    *,
    artist_id: str,
    artist_name: str,
    language: str,
    site: str,
    artist_url: str,
    raw_output_dir: str,
    manifest_output_path: str,
    sources: list[dict[str, Any]],
    request_delay_seconds: float = 0.0,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "artist_name": artist_name,
        "language": language,
        "source_type": "web_scrape",
        "collection_method": f"Discography scrape manifest discovered from {site} artist page: {artist_url}",
        "raw_output_dir": raw_output_dir,
        "manifest_output_path": manifest_output_path,
        "respect_robots_txt": True,
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "request_delay_seconds": request_delay_seconds,
        "user_agent": DEFAULT_USER_AGENT,
        "sources": sources,
    }


def discover_discography_manifest(
    *,
    artist_id: str,
    artist_name: str,
    language: str,
    site: str,
    artist_url: str,
    output_path: Path,
    raw_output_dir: str,
    manifest_output_path: str,
    request_delay_seconds: float = 0.0,
) -> DiscographyDiscoverySummary:
    sources = discover_discography_sources(
        site,
        artist_url,
        request_delay_seconds=request_delay_seconds,
    )

    payload = build_discography_manifest_payload(
        artist_id=artist_id,
        artist_name=artist_name,
        language=language,
        site=site,
        artist_url=artist_url,
        raw_output_dir=raw_output_dir,
        manifest_output_path=manifest_output_path,
        sources=sources,
        request_delay_seconds=request_delay_seconds,
    )
    write_web_manifest(output_path, payload)
    return DiscographyDiscoverySummary(
        output_path=output_path,
        site=site,
        source_url=artist_url,
        track_count=len(sources),
    )
