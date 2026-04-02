from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

from src.akira_engine.ingest import (
    build_manifest_payload,
    relative_manifest_path,
    slugify,
    write_manifest,
)


DEFAULT_USER_AGENT = "AKIRA-ENGINE/1.0 (local lyric research pipeline)"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF_SECONDS = 2.0
LYRIC_HINT_PATTERN = re.compile(r"(lyric|lyrics|kashi|uta|song[-_ ]?text|song[-_ ]?lyric)", re.IGNORECASE)
TRACK_BLOCK_TAGS = ("div", "section", "article", "main", "p")
REQUIRED_WEB_MANIFEST_KEYS = {
    "schema_version",
    "artist_id",
    "artist_name",
    "language",
    "sources",
}


@dataclass(frozen=True)
class SitePreset:
    name: str
    selectors: list[str] = field(default_factory=list)
    remove_selectors: list[str] = field(default_factory=list)


SITE_PRESETS = {
    "uta-net.com": SitePreset(name="uta_net", selectors=["#kashi-area"]),
    "www.uta-net.com": SitePreset(name="uta_net", selectors=["#kashi-area"]),
    "utaten.com": SitePreset(
        name="utaten",
        selectors=["div.lyricBody div.hiragana"],
        remove_selectors=["span.rt"],
    ),
    "www.utaten.com": SitePreset(
        name="utaten",
        selectors=["div.lyricBody div.hiragana"],
        remove_selectors=["span.rt"],
    ),
    "petitlyrics.com": SitePreset(name="petitlyrics"),
    "www.petitlyrics.com": SitePreset(name="petitlyrics"),
}


@dataclass
class ScrapedTrackSummary:
    track_id: str
    title: str
    raw_output_path: Path
    source_url: str
    extraction_mode: str


@dataclass
class WebScrapeSummary:
    raw_output_dir: Path
    manifest_path: Path
    track_count: int
    tracks: list[ScrapedTrackSummary]


def load_web_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_WEB_MANIFEST_KEYS - manifest.keys())
    if missing:
        raise ValueError(f"Web manifest is missing required keys: {', '.join(missing)}")
    if not manifest["sources"]:
        raise ValueError("Web manifest has no sources.")
    return manifest


def default_raw_output_dir(artist_id: str) -> Path:
    return Path("lyrics") / "raw" / artist_id


def default_manifest_output_path(artist_id: str) -> Path:
    return Path("lyrics") / "manifests" / f"{artist_id}_manifest.json"


def resolve_output_path(path_value: str | Path, base_dir: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def build_requests_session(user_agent: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})
    return session


def robots_url_for(source_url: str) -> str:
    parsed = urlparse(source_url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def is_allowed_by_robots(source_url: str, user_agent: str) -> bool:
    parser = RobotFileParser()
    parser.set_url(robots_url_for(source_url))
    try:
        parser.read()
    except Exception:
        return True
    return parser.can_fetch(user_agent, source_url)


def retry_delay_seconds(retry_after: str | None, attempt: int, backoff_seconds: float) -> float:
    if retry_after:
        try:
            return max(float(retry_after), backoff_seconds)
        except ValueError:
            pass
    return backoff_seconds * (attempt + 1)


def fetch_html(
    session: requests.Session,
    source_url: str,
    timeout_seconds: int,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
) -> str:
    for attempt in range(max_retries + 1):
        try:
            response = session.get(source_url, timeout=timeout_seconds)
            if response.status_code == 429 and attempt < max_retries:
                time.sleep(
                    retry_delay_seconds(
                        response.headers.get("Retry-After"),
                        attempt,
                        retry_backoff_seconds,
                    )
                )
                continue
            response.raise_for_status()
            return response.text
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code in {429, 500, 502, 503, 504} and attempt < max_retries:
                time.sleep(
                    retry_delay_seconds(
                        exc.response.headers.get("Retry-After") if exc.response is not None else None,
                        attempt,
                        retry_backoff_seconds,
                    )
                )
                continue
            raise
        except (requests.Timeout, requests.ConnectionError):
            if attempt < max_retries:
                time.sleep(retry_backoff_seconds * (attempt + 1))
                continue
            raise

    raise RuntimeError(f"Failed to fetch {source_url}")


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def domain_from_url(source_url: str) -> str:
    return urlparse(source_url).netloc.lower()


def preset_for_source(source: dict[str, Any]) -> SitePreset | None:
    explicit = source.get("site_preset")
    if explicit:
        for preset in SITE_PRESETS.values():
            if preset.name == explicit:
                return preset
    return SITE_PRESETS.get(domain_from_url(source["url"]))


def text_from_element(element: Tag) -> str:
    working = BeautifulSoup(str(element), "html.parser")
    for removable in working.select("script, style, noscript"):
        removable.decompose()
    for br in working.find_all("br"):
        br.replace_with("\n")
    text = working.get_text("\n")
    text = text.replace("\xa0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    cleaned_lines: list[str] = []
    blank_open = False
    for line in lines:
        if line:
            cleaned_lines.append(line)
            blank_open = False
            continue
        if not blank_open and cleaned_lines:
            cleaned_lines.append("")
            blank_open = True
    return "\n".join(cleaned_lines).strip()


def lyric_text_from_element(
    element: Tag,
    *,
    remove_selectors: list[str] | None = None,
) -> str:
    working = BeautifulSoup(str(element), "html.parser")
    for removable in working.select("script, style, noscript"):
        removable.decompose()
    for selector in remove_selectors or []:
        for removable in working.select(selector):
            removable.decompose()
    for br in working.find_all("br"):
        br.replace_with("\n")

    text = working.get_text("")
    return normalize_scraped_text(text)


def tree_text_from_element(
    element: Tag,
    *,
    skip_classes: set[str] | None = None,
    block_tags: set[str] | None = None,
) -> str:
    skip_classes = skip_classes or set()
    block_tags = block_tags or {"div", "p", "li", "section", "article"}
    parts: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, NavigableString):
            parts.append(str(node))
            return
        if not isinstance(node, Tag):
            return
        if node.name in {"script", "style", "noscript"}:
            return
        if node.name == "br":
            parts.append("\n")
            for child in node.children:
                walk(child)
            return
        if skip_classes.intersection(set(node.get("class", []))):
            return
        for child in node.children:
            walk(child)
        if node.name in block_tags:
            parts.append("\n")

    walk(element)
    return normalize_scraped_text("".join(parts))


def inline_text_with_breaks(
    element: Tag,
    *,
    skip_classes: set[str] | None = None,
) -> str:
    skip_classes = skip_classes or set()
    parts: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, NavigableString):
            text = str(node)
            if text.strip():
                parts.append(text)
            return
        if not isinstance(node, Tag):
            return
        if node.name in {"script", "style", "noscript"}:
            return
        if skip_classes.intersection(set(node.get("class", []))):
            return
        if node.name == "br":
            parts.append("\n")
            for child in node.children:
                walk(child)
            return
        for child in node.children:
            walk(child)

    walk(element)
    return normalize_scraped_text("".join(parts))


def recursive_json_walk(payload: Any) -> list[Any]:
    values: list[Any] = []
    if isinstance(payload, dict):
        values.append(payload)
        for value in payload.values():
            values.extend(recursive_json_walk(value))
    elif isinstance(payload, list):
        for item in payload:
            values.extend(recursive_json_walk(item))
    return values


def extract_json_ld_lyrics(soup: BeautifulSoup) -> str | None:
    for script in soup.select('script[type="application/ld+json"]'):
        raw_text = script.string or script.get_text()
        if not raw_text.strip():
            continue
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            continue
        for node in recursive_json_walk(payload):
            if isinstance(node, dict) and isinstance(node.get("lyrics"), str):
                candidate = normalize_scraped_text(node["lyrics"])
                if candidate:
                    return candidate
    return None


def extract_from_selectors(
    soup: BeautifulSoup,
    selectors: list[str],
    *,
    remove_selectors: list[str] | None = None,
) -> str | None:
    chunks: list[str] = []
    for selector in selectors:
        for element in soup.select(selector):
            text = lyric_text_from_element(element, remove_selectors=remove_selectors)
            if text:
                chunks.append(text)
    candidate = normalize_scraped_text("\n\n".join(chunks))
    return candidate or None


def extract_petitlyrics_lyrics(soup: BeautifulSoup) -> str | None:
    canvas = soup.select_one("canvas#lyrics")
    if canvas is not None:
        canvas_text = normalize_scraped_text(canvas.get_text("\n"))
        if canvas_text:
            return canvas_text

    root = soup.select_one("table#lyrics_list td")
    if root is None:
        return None

    lyric_blocks: list[tuple[int, Tag]] = []
    for child in root.find_all("div", recursive=False):
        text = lyric_text_from_element(child)
        if len(text) < 120:
            continue
        lyric_blocks.append((len(text), child))

    if not lyric_blocks:
        return None

    lyric_blocks.sort(key=lambda item: item[0], reverse=True)
    return lyric_text_from_element(lyric_blocks[0][1])


def extract_with_site_preset(soup: BeautifulSoup, preset: SitePreset) -> str | None:
    if preset.name == "petitlyrics":
        return extract_petitlyrics_lyrics(soup)
    if preset.name == "utaten":
        element = soup.select_one("div.lyricBody div.hiragana")
        if element is None:
            return None
        return inline_text_with_breaks(element, skip_classes={"rt"})
    if preset.name == "uta_net":
        element = soup.select_one("#kashi-area")
        if element is None:
            return None
        return tree_text_from_element(element)
    if preset.selectors:
        return extract_from_selectors(
            soup,
            preset.selectors,
            remove_selectors=preset.remove_selectors,
        )
    return None


def score_candidate_element(element: Tag) -> float:
    if not isinstance(element, Tag):
        return 0.0
    attrs = " ".join(
        [
            element.get("id", ""),
            " ".join(element.get("class", [])),
            element.name or "",
        ]
    )
    text = text_from_element(element)
    if not text:
        return 0.0

    lines = [line for line in text.splitlines() if line.strip()]
    line_count = len(lines)
    if line_count < 4:
        return 0.0

    hint_bonus = 30.0 if LYRIC_HINT_PATTERN.search(attrs) else 0.0
    br_bonus = float(len(element.find_all("br"))) * 1.5
    line_bonus = min(float(line_count), 25.0)
    length_bonus = min(len(text) / 50.0, 20.0)
    anchor_penalty = float(len(element.find_all("a"))) * 1.0
    list_penalty = 10.0 if element.name in {"nav", "header", "footer"} else 0.0

    return hint_bonus + br_bonus + line_bonus + length_bonus - anchor_penalty - list_penalty


def extract_heuristic_lyrics(soup: BeautifulSoup) -> str | None:
    candidates: list[tuple[float, Tag]] = []
    for element in soup.find_all(TRACK_BLOCK_TAGS):
        score = score_candidate_element(element)
        if score <= 0:
            continue
        candidates.append((score, element))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    best_text = text_from_element(candidates[0][1])
    candidate = normalize_scraped_text(best_text)
    return candidate or None


def normalize_scraped_text(text: str) -> str:
    normalized = text.replace("\xa0", " ")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.splitlines()]
    cleaned_lines: list[str] = []
    previous_blank = True
    for line in lines:
        if line:
            cleaned_lines.append(line)
            previous_blank = False
            continue
        if not previous_blank and cleaned_lines:
            cleaned_lines.append("")
            previous_blank = True
    return "\n".join(cleaned_lines).strip()


def infer_title(soup: BeautifulSoup, source: dict[str, Any], index: int) -> str:
    if source.get("title"):
        return source["title"]
    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        return str(og_title["content"]).strip()
    title_tag = soup.find("title")
    if title_tag:
        title_text = title_tag.get_text(strip=True)
        if title_text:
            return title_text
    heading = soup.find(["h1", "h2"])
    if heading:
        heading_text = heading.get_text(strip=True)
        if heading_text:
            return heading_text
    return f"track {index:02d}"


def infer_track_id(title: str, explicit_track_id: str | None, index: int, used_track_ids: set[str]) -> str:
    base_id = explicit_track_id or slugify(title)
    if base_id == "untitled":
        base_id = f"track_{index:02d}"

    candidate = base_id
    suffix = 2
    while candidate in used_track_ids:
        candidate = f"{base_id}_{suffix:02d}"
        suffix += 1
    used_track_ids.add(candidate)
    return candidate


def extract_lyrics_from_html(
    html: str,
    source: dict[str, Any],
) -> tuple[str, str]:
    soup = parse_html(html)
    extraction_mode = str(source.get("extraction_mode", "auto"))
    preset = preset_for_source(source)

    selector = source.get("selector")
    selectors = source.get("selectors", [])
    if selector:
        selectors = [selector] + list(selectors)
    if not selectors and preset and preset.selectors:
        selectors = list(preset.selectors)
    remove_selectors = list(source.get("remove_selectors", []))
    if preset:
        remove_selectors = list(dict.fromkeys(remove_selectors + preset.remove_selectors))

    if extraction_mode == "json_ld":
        lyrics = extract_json_ld_lyrics(soup)
        if not lyrics:
            raise ValueError("No lyrics found in JSON-LD.")
        return lyrics, "json_ld"

    if extraction_mode == "selector":
        if not selectors:
            raise ValueError("selector mode requires selector or selectors.")
        lyrics = extract_from_selectors(soup, selectors, remove_selectors=remove_selectors)
        if not lyrics:
            raise ValueError("No lyrics found with the provided selectors.")
        return lyrics, "selector"

    if extraction_mode == "auto":
        if preset:
            lyrics = extract_with_site_preset(soup, preset)
            if lyrics:
                return lyrics, f"preset:{preset.name}"
        if selectors:
            lyrics = extract_from_selectors(soup, selectors, remove_selectors=remove_selectors)
            if lyrics:
                return lyrics, "selector"
        lyrics = extract_json_ld_lyrics(soup)
        if lyrics:
            return lyrics, "json_ld"
        lyrics = extract_heuristic_lyrics(soup)
        if lyrics:
            return lyrics, "heuristic"
        raise ValueError("No lyrics found via auto extraction.")

    if extraction_mode == "heuristic":
        lyrics = extract_heuristic_lyrics(soup)
        if not lyrics:
            raise ValueError("No lyrics found via heuristic extraction.")
        return lyrics, "heuristic"

    raise ValueError(f"Unsupported extraction_mode: {extraction_mode}")


def source_site_from_url(source_url: str) -> str:
    return urlparse(source_url).netloc


def scrape_web_manifest(
    web_manifest_path: Path,
    *,
    raw_output_dir: Path | None = None,
    manifest_output_path: Path | None = None,
    overwrite: bool = False,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> WebScrapeSummary:
    web_manifest = load_web_manifest(web_manifest_path)
    artist_id = web_manifest["artist_id"]
    artist_name = web_manifest["artist_name"]
    language = web_manifest["language"]
    source_type = web_manifest.get("source_type", "web_scrape")
    collection_method = web_manifest.get(
        "collection_method",
        "Web scrape from user-supplied lyric URLs with selector and heuristic extraction.",
    )
    user_agent = web_manifest.get("user_agent", DEFAULT_USER_AGENT)
    timeout_seconds = int(web_manifest.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS))
    respect_robots = bool(web_manifest.get("respect_robots_txt", True))
    request_delay_seconds = float(web_manifest.get("request_delay_seconds", 0.0))
    base_dir = web_manifest_path.parent

    resolved_raw_dir = raw_output_dir or resolve_output_path(
        web_manifest.get("raw_output_dir", default_raw_output_dir(artist_id)),
        base_dir,
    )
    resolved_manifest_path = manifest_output_path or resolve_output_path(
        web_manifest.get("manifest_output_path", default_manifest_output_path(artist_id)),
        base_dir,
    )

    resolved_raw_dir.mkdir(parents=True, exist_ok=True)
    session = build_requests_session(user_agent)

    manifest_tracks: list[dict[str, Any]] = []
    track_summaries: list[ScrapedTrackSummary] = []
    used_track_ids: set[str] = set()

    for index, source in enumerate(web_manifest["sources"], start=1):
        if index > 1 and request_delay_seconds > 0:
            time.sleep(request_delay_seconds)
        source_url = source["url"]
        if progress_callback:
            progress_callback(
                {
                    "event": "source_start",
                    "artist_id": artist_id,
                    "index": index,
                    "total_sources": len(web_manifest["sources"]),
                    "source_url": source_url,
                    "source_title": source.get("title"),
                }
            )
        if respect_robots and not is_allowed_by_robots(source_url, user_agent):
            raise SystemExit(f"Blocked by robots.txt: {source_url}")

        html = fetch_html(session, source_url, timeout_seconds)
        soup = parse_html(html)
        title = infer_title(soup, source, index)
        track_id = infer_track_id(source.get("title", title), source.get("track_id"), index, used_track_ids)
        lyrics_text, extraction_mode = extract_lyrics_from_html(html, source)

        output_path = resolved_raw_dir / f"{track_id}.txt"
        if output_path.exists() and not overwrite:
            raise SystemExit(
                f"Raw lyric file already exists: {output_path}\n"
                "Use overwrite mode or remove the file before rerunning."
            )
        output_path.write_text(lyrics_text + "\n", encoding="utf-8")

        manifest_tracks.append(
            {
                "track_id": track_id,
                "title": source.get("title", title),
                "lyric_path": relative_manifest_path(output_path, resolved_manifest_path.parent),
                "source_url": source_url,
                "source_site": source_site_from_url(source_url),
                "notes": (
                    f"Scraped from {source_url} via {extraction_mode} extraction."
                    + (f" {source['notes']}" if source.get("notes") else "")
                ),
            }
        )
        track_summaries.append(
            ScrapedTrackSummary(
                track_id=track_id,
                title=source.get("title", title),
                raw_output_path=output_path,
                source_url=source_url,
                extraction_mode=extraction_mode,
            )
        )
        if progress_callback:
            progress_callback(
                {
                    "event": "source_complete",
                    "artist_id": artist_id,
                    "index": index,
                    "total_sources": len(web_manifest["sources"]),
                    "track_id": track_id,
                    "source_url": source_url,
                    "output_path": str(output_path),
                }
            )

    manifest_payload = build_manifest_payload(
        artist_id=artist_id,
        artist_name=artist_name,
        language=language,
        source_type=source_type,
        collection_method=collection_method,
        tracks=manifest_tracks,
    )
    write_manifest(resolved_manifest_path, manifest_payload)
    if progress_callback:
        progress_callback(
            {
                "event": "manifest_complete",
                "artist_id": artist_id,
                "manifest_path": str(resolved_manifest_path),
                "track_count": len(track_summaries),
            }
        )
    return WebScrapeSummary(
        raw_output_dir=resolved_raw_dir,
        manifest_path=resolved_manifest_path,
        track_count=len(track_summaries),
        tracks=track_summaries,
    )
