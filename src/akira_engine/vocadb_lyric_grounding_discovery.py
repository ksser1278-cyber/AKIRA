from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from .training_data import write_json


VOCADB_API_ROOT = "https://vocadb.net/api"
VOCADB_USER_AGENT = "AKIRA-ENGINE/1.0 vocadb-lyric-grounding-discovery"
UTATEN_SEARCH_URL = "https://utaten.com/search"
DISCOVERY_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36"
TRUSTED_SOURCE_LABEL = "UtaTen lyrics page"
TRUSTED_SOURCE_TYPE = "trusted_lyric_db"


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _vocadb_get_json(path: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urllib.parse.urlencode({key: value for key, value in params.items() if value is not None})
    url = f"{VOCADB_API_ROOT}{path}?{query}" if query else f"{VOCADB_API_ROOT}{path}"
    request = urllib.request.Request(url, headers={"User-Agent": VOCADB_USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _fetch_vocadb_song(track_id: str) -> dict[str, Any]:
    song_id = int(track_id.replace("vocadb_", "", 1))
    return _vocadb_get_json(
        f"/songs/{song_id}",
        {
            "fields": "Artists,Names,PVs",
            "lang": "Default",
        },
    )


def _normalize_for_match(text: str) -> str:
    normalized = unescape(_safe_text(text)).casefold()
    normalized = re.sub(r"\s+", "", normalized)
    normalized = re.sub(r"[\"'`“”‘’\[\](){}:;,.!?・／/\\\-_=+~*#@&%$^|<>]", "", normalized)
    normalized = normalized.replace("feat", "")
    normalized = normalized.replace("featuring", "")
    return normalized


def _vocadb_song_title(song: dict[str, Any]) -> str:
    return _safe_text(song.get("defaultName")) or _safe_text(song.get("name"))


def _vocadb_producer_names(song: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for artist_entry in song.get("artists", []):
        categories = _safe_text(artist_entry.get("categories")).lower()
        if "producer" not in categories and "composer" not in categories and "band" not in categories:
            continue
        artist = artist_entry.get("artist", {})
        name = _safe_text(artist.get("name")) or _safe_text(artist_entry.get("name"))
        if name:
            names.append(name)
    return names


def _vocadb_voicebank_names(song: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for artist_entry in song.get("artists", []):
        categories = _safe_text(artist_entry.get("categories")).lower()
        if "vocalist" not in categories:
            continue
        artist = artist_entry.get("artist", {})
        name = _safe_text(artist.get("name")) or _safe_text(artist_entry.get("name"))
        if name:
            names.append(name)
    return names


def _title_variants(title: str) -> list[str]:
    variants = [_safe_text(title)]
    stripped = re.sub(r"[★☆「」『』【】\[\]()（）]", "", title)
    stripped = _safe_text(stripped)
    if stripped and stripped not in variants:
        variants.append(stripped)
    compact = _safe_text(re.sub(r"\s+", "", stripped or title))
    if compact and compact not in variants:
        variants.append(compact)
    return [value for value in variants if value]


def _utaten_rows_from_response(response_text: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(response_text, "html.parser")
    rows: list[dict[str, str]] = []
    for row in soup.select("table.searchResult.artistLyricList tr")[1:]:
        title_link = row.select_one("p.searchResult__title a[href*='/lyric/']")
        artist_link = row.select_one("td.searchResult__artist p a")
        writer_block = row.select_one("td.searchResult__artist")
        if not title_link:
            continue
        href = _safe_text(title_link.get("href"))
        if not href.startswith("/lyric/"):
            continue
        rows.append(
            {
                "title": title_link.get_text(" ", strip=True),
                "artist": artist_link.get_text(" ", strip=True) if artist_link else "",
                "writer_blob": writer_block.get_text(" ", strip=True) if writer_block else "",
                "url": urllib.parse.urljoin("https://utaten.com", href),
            }
        )
    return rows


def _search_utaten(params: dict[str, str]) -> list[dict[str, str]]:
    response = requests.get(
        "https://utaten.com/lyric/search",
        params={"sort": "popular_sort_asc", **params},
        headers={"User-Agent": DISCOVERY_USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    return _utaten_rows_from_response(response.text)


def _score_candidate(song: dict[str, Any], candidate: dict[str, str]) -> int:
    score = 0
    title = _normalize_for_match(_vocadb_song_title(song))
    candidate_title = _normalize_for_match(candidate.get("title", ""))
    if candidate_title == title:
        score += 100
    elif title and (title in candidate_title or candidate_title in title):
        score += 60

    producer_tokens = {_normalize_for_match(name) for name in _vocadb_producer_names(song) if _normalize_for_match(name)}
    artist_blob = _normalize_for_match(candidate.get("artist", ""))
    writer_blob = _normalize_for_match(candidate.get("writer_blob", ""))
    for token in producer_tokens:
        if token and token in artist_blob:
            score += 25
        if token and token in writer_blob:
            score += 25
    return score


def _search_candidates(song: dict[str, Any]) -> list[dict[str, str]]:
    titles = _title_variants(_vocadb_song_title(song))
    producers = _vocadb_producer_names(song)[:2]
    voicebanks = _vocadb_voicebank_names(song)[:2]
    query_params: list[dict[str, str]] = []
    for title in titles:
        query_params.append({"title": title})
        for producer in producers:
            query_params.append({"title": title, "artist_name": producer})
            query_params.append({"title": title, "composer": producer})
        for voicebank in voicebanks:
            query_params.append({"title": title, "artist_name": voicebank})

    seen_keys: set[tuple[str, str, str]] = set()
    deduped: list[dict[str, str]] = []
    for params in query_params:
        try:
            rows = _search_utaten(params)
        except Exception:
            continue
        for row in rows:
            key = (row.get("url", ""), row.get("title", ""), row.get("artist", ""))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduped.append(row)
    return deduped


def discover_trusted_lyric_urls_for_workspace(
    *,
    workspace_root: Path,
    min_score: int = 100,
) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    incoming_dir = workspace_root / "incoming"
    discovered: dict[str, dict[str, Any]] = {}
    skipped: list[dict[str, Any]] = []

    for record_path in sorted(incoming_dir.glob("vocadb_*.json")):
        record = _load_json(record_path)
        track_id = _safe_text(record.get("track_identity", {}).get("track_id")) or record_path.stem

        lyric_sources = list(record.get("grounding_sources", {}).get("lyric_sources", []))
        if lyric_sources:
            skipped.append({"track_id": track_id, "reason": "already_has_lyric_sources"})
            continue

        try:
            song = _fetch_vocadb_song(track_id)
            candidates = _search_candidates(song)
        except Exception as exc:
            skipped.append({"track_id": track_id, "reason": f"discovery_failed:{type(exc).__name__}"})
            continue

        best_candidate: dict[str, str] | None = None
        best_score = -1
        for candidate in candidates:
            score = _score_candidate(song, candidate)
            if score > best_score:
                best_score = score
                best_candidate = candidate

        if not best_candidate or best_score < min_score:
            skipped.append({"track_id": track_id, "reason": f"no_match:min_score:{best_score}"})
            continue

        discovered[track_id] = {
            "lyric_url": best_candidate["url"],
            "label": TRUSTED_SOURCE_LABEL,
            "source_type": TRUSTED_SOURCE_TYPE,
            "notes": f"Auto-discovered from UtaTen title search with score {best_score}.",
            "match_score": best_score,
            "matched_title": best_candidate["title"],
            "matched_artist": best_candidate["artist"],
        }

    manifest = {
        "schema_version": "1.0",
        "record_type": "vocadb_lyric_grounding_discovery_manifest",
        "workspace_root": str(workspace_root),
        "counts": {
            "discovered": len(discovered),
            "skipped": len(skipped),
        },
        "discovered": discovered,
        "skipped": skipped,
    }
    discovered_path = write_json(workspace_root / "trusted_lyric_url_map.auto.json", discovered)
    manifest["trusted_lyric_url_map_path"] = str(discovered_path)
    manifest_path = write_json(workspace_root / "vocadb_lyric_grounding_discovery_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
