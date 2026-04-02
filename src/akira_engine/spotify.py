from __future__ import annotations

import base64
import json
import os
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


SPOTIFY_ACCOUNTS_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"
DEFAULT_ENV_PATH = Path("config") / ".env"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_MAX_RETRIES = 4
DEFAULT_RETRY_BACKOFF_SECONDS = 2.0
BRACKET_PAIRS = {
    "(": ")",
    "[": "]",
    "{": "}",
}
VARIANT_TITLE_MARKERS = (
    "instrumental",
    "remix",
    "extended mix",
    "piano ver",
    "strings ver",
    "acoustic ver",
    "off vocal",
    "karaoke",
)
VARIANT_TITLE_SEPARATORS = (" / ", " - ")


def parse_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def env_value(name: str, env_path: Path | None = None) -> str | None:
    direct = os.getenv(name)
    if direct:
        return direct
    values = parse_dotenv(env_path or DEFAULT_ENV_PATH)
    return values.get(name)


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower().strip()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[\"'`]", "", value)
    value = remove_bracketed_segments(value)
    value = re.sub(r"[!?,.:;~/\\\-]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def remove_bracketed_segments(value: str) -> str:
    result: list[str] = []
    stack: list[str] = []

    for character in value:
        if character in BRACKET_PAIRS:
            stack.append(BRACKET_PAIRS[character])
            continue
        if stack and character == stack[-1]:
            stack.pop()
            continue
        if not stack:
            result.append(character)

    return "".join(result)


def is_variant_suffix(normalized_suffix: str) -> bool:
    return any(marker in normalized_suffix for marker in VARIANT_TITLE_MARKERS)


def candidate_base_titles(title: str) -> list[str]:
    normalized = normalize_title(title)
    if not normalized:
        return []

    keys = [normalized]
    for separator in VARIANT_TITLE_SEPARATORS:
        if separator not in title:
            continue
        base_title, suffix = title.split(separator, 1)
        normalized_suffix = normalize_title(suffix)
        if not is_variant_suffix(normalized_suffix):
            continue
        base_normalized = normalize_title(base_title)
        if base_normalized and base_normalized not in keys:
            keys.append(base_normalized)
    return keys


def is_redundant_variant_title(title: str, known_titles: set[str] | None = None) -> bool:
    candidate_titles = candidate_base_titles(title)
    if len(candidate_titles) <= 1:
        return False
    if known_titles is None:
        return True
    return any(base_title in known_titles for base_title in candidate_titles[1:])


@dataclass
class SpotifyArtistMatch:
    artist_id: str
    name: str
    popularity: int
    followers: int
    genres: list[str]
    url: str


class SpotifyClient:
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self._access_token: str | None = None

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "SpotifyClient":
        client_id = env_value("SPOTIFY_CLIENT_ID", env_path)
        client_secret = env_value("SPOTIFY_CLIENT_SECRET", env_path)
        if not client_id or not client_secret:
            raise ValueError("Spotify credentials were not found in environment or config/.env.")
        return cls(client_id=client_id, client_secret=client_secret)

    def _auth_headers(self) -> dict[str, str]:
        token = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _api_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token()}"}

    def _retry_delay_seconds(self, retry_after: str | None, attempt: int) -> float:
        if retry_after:
            try:
                return max(float(retry_after), self.retry_backoff_seconds)
            except ValueError:
                pass
        return self.retry_backoff_seconds * (attempt + 1)

    def access_token(self) -> str:
        if self._access_token is not None:
            return self._access_token

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    SPOTIFY_ACCOUNTS_URL,
                    headers=self._auth_headers(),
                    data={"grant_type": "client_credentials"},
                    timeout=self.timeout_seconds,
                )
                if response.status_code == 429 and attempt < self.max_retries:
                    time.sleep(self._retry_delay_seconds(response.headers.get("Retry-After"), attempt))
                    continue
                response.raise_for_status()
                payload = response.json()
                self._access_token = payload["access_token"]
                return self._access_token
            except requests.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                    time.sleep(
                        self._retry_delay_seconds(
                            exc.response.headers.get("Retry-After") if exc.response is not None else None,
                            attempt,
                        )
                    )
                    continue
                raise
            except (requests.Timeout, requests.ConnectionError):
                if attempt < self.max_retries:
                    time.sleep(self._retry_delay_seconds(None, attempt))
                    continue
                raise

        raise RuntimeError("Failed to obtain Spotify access token after retries.")

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        allow_reauth = True
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(
                    f"{SPOTIFY_API_BASE_URL}{path}",
                    headers=self._api_headers(),
                    params=params,
                    timeout=self.timeout_seconds,
                )
                if response.status_code == 401 and allow_reauth:
                    self._access_token = None
                    allow_reauth = False
                    continue
                if response.status_code == 429 and attempt < self.max_retries:
                    time.sleep(self._retry_delay_seconds(response.headers.get("Retry-After"), attempt))
                    continue
                response.raise_for_status()
                return response.json()
            except requests.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                    time.sleep(
                        self._retry_delay_seconds(
                            exc.response.headers.get("Retry-After") if exc.response is not None else None,
                            attempt,
                        )
                    )
                    continue
                raise
            except (requests.Timeout, requests.ConnectionError):
                if attempt < self.max_retries:
                    time.sleep(self._retry_delay_seconds(None, attempt))
                    continue
                raise

        raise RuntimeError(f"Spotify GET {path} failed after retries.")

    def paged_items(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        item_key: str = "items",
    ) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        working_params = dict(params or {})
        offset = int(working_params.get("offset", 0))
        limit = int(working_params.get("limit", 50))

        while True:
            payload = self.get(path, params={**working_params, "offset": offset, "limit": limit})
            items = payload.get(item_key, [])
            collected.extend(items)
            if payload.get("next") is None:
                break
            offset += limit
        return collected

    def search_artist(self, artist_name: str, *, limit: int = 10) -> list[SpotifyArtistMatch]:
        payload = self.get("/search", params={"q": artist_name, "type": "artist", "limit": limit})
        matches: list[SpotifyArtistMatch] = []
        for item in payload.get("artists", {}).get("items", []):
            matches.append(
                SpotifyArtistMatch(
                    artist_id=item["id"],
                    name=item["name"],
                    popularity=int(item.get("popularity", 0)),
                    followers=int(item.get("followers", {}).get("total", 0)),
                    genres=list(item.get("genres", [])),
                    url=item.get("external_urls", {}).get("spotify", ""),
                )
            )
        return matches

    def get_artist(self, artist_id: str) -> dict[str, Any]:
        return self.get(f"/artists/{artist_id}")

    def get_artist_albums(
        self,
        artist_id: str,
        *,
        include_groups: str = "album,single,compilation",
        market: str = "JP",
    ) -> list[dict[str, Any]]:
        albums = self.paged_items(
            f"/artists/{artist_id}/albums",
            params={"include_groups": include_groups, "market": market, "limit": 10},
        )
        deduped: dict[str, dict[str, Any]] = {}
        for album in albums:
            deduped[album["id"]] = album
        return sorted(deduped.values(), key=lambda item: (item.get("release_date", ""), item["name"]))

    def get_album_tracks(self, album_id: str, *, market: str = "JP") -> list[dict[str, Any]]:
        return self.paged_items(
            f"/albums/{album_id}/tracks",
            params={"market": market, "limit": 50},
        )


def choose_best_artist_match(matches: list[SpotifyArtistMatch], requested_name: str) -> SpotifyArtistMatch:
    if not matches:
        raise ValueError(f"No Spotify artist matches were found for '{requested_name}'.")
    normalized_requested = normalize_title(requested_name)
    exact = [match for match in matches if normalize_title(match.name) == normalized_requested]
    ranked = exact or matches
    ranked = sorted(ranked, key=lambda item: (-item.popularity, -item.followers, item.name))
    return ranked[0]


def build_artist_discography_snapshot(
    *,
    client: SpotifyClient,
    artist_id: str,
    market: str = "JP",
    include_groups: str = "album,single,compilation",
) -> dict[str, Any]:
    artist = client.get_artist(artist_id)
    albums = client.get_artist_albums(artist_id, include_groups=include_groups, market=market)

    releases: list[dict[str, Any]] = []
    canonical_titles: dict[str, dict[str, Any]] = {}
    raw_track_total = 0

    for album in albums:
        tracks = client.get_album_tracks(album["id"], market=market)
        release_tracks: list[dict[str, Any]] = []
        for track in tracks:
            raw_track_total += 1
            track_payload = {
                "track_id": track["id"],
                "name": track["name"],
                "normalized_name": normalize_title(track["name"]),
                "disc_number": track.get("disc_number"),
                "track_number": track.get("track_number"),
                "duration_ms": track.get("duration_ms"),
                "explicit": track.get("explicit", False),
                "spotify_url": track.get("external_urls", {}).get("spotify", ""),
            }
            release_tracks.append(track_payload)

            normalized_name = track_payload["normalized_name"]
            if normalized_name not in canonical_titles:
                canonical_titles[normalized_name] = {
                    "name": track["name"],
                    "normalized_name": normalized_name,
                    "first_release_date": album.get("release_date", ""),
                    "spotify_track_id": track["id"],
                    "albums": [album["name"]],
                }
            else:
                canonical_titles[normalized_name]["albums"].append(album["name"])

        releases.append(
            {
                "album_id": album["id"],
                "name": album["name"],
                "album_type": album.get("album_type", ""),
                "release_date": album.get("release_date", ""),
                "release_date_precision": album.get("release_date_precision", ""),
                "total_tracks": album.get("total_tracks"),
                "spotify_url": album.get("external_urls", {}).get("spotify", ""),
                "tracks": release_tracks,
            }
        )

    canonical_track_list = sorted(canonical_titles.values(), key=lambda item: (item["first_release_date"], item["name"]))
    spotify_normalized_titles = {track["normalized_name"] for track in canonical_track_list if track["normalized_name"]}
    redundant_variants = [
        track
        for track in canonical_track_list
        if is_redundant_variant_title(track["name"], spotify_normalized_titles)
    ]
    redundant_variant_titles = {track["normalized_name"] for track in redundant_variants}
    primary_lyric_tracks = [
        track for track in canonical_track_list if track["normalized_name"] not in redundant_variant_titles
    ]

    return {
        "schema_version": "1.0",
        "artist": {
            "spotify_artist_id": artist["id"],
            "name": artist["name"],
            "followers": artist.get("followers", {}).get("total", 0),
            "popularity": artist.get("popularity", 0),
            "genres": artist.get("genres", []),
            "spotify_url": artist.get("external_urls", {}).get("spotify", ""),
        },
        "market": market,
        "include_groups": include_groups,
        "release_count": len(releases),
        "raw_track_total": raw_track_total,
        "canonical_track_count": len(canonical_track_list),
        "primary_lyric_track_count": len(primary_lyric_tracks),
        "redundant_variant_track_count": len(redundant_variants),
        "canonical_tracks": canonical_track_list,
        "primary_lyric_tracks": primary_lyric_tracks,
        "redundant_variant_tracks": redundant_variants,
        "releases": releases,
    }


def compare_lyric_manifest_to_spotify(
    lyric_manifest: dict[str, Any],
    spotify_snapshot: dict[str, Any],
) -> dict[str, Any]:
    lyric_tracks = lyric_manifest.get("tracks", [])
    lyric_by_normalized: dict[str, dict[str, Any]] = {}
    for track in lyric_tracks:
        normalized_name = normalize_title(track["title"])
        if normalized_name:
            lyric_by_normalized[normalized_name] = track

    spotify_tracks = spotify_snapshot.get("canonical_tracks", [])
    spotify_by_normalized = {track["normalized_name"]: track for track in spotify_tracks if track["normalized_name"]}

    strict_missing_from_lyrics = [
        track
        for normalized_name, track in spotify_by_normalized.items()
        if normalized_name not in lyric_by_normalized
    ]
    lyric_missing_from_spotify = [
        track
        for normalized_name, track in lyric_by_normalized.items()
        if normalized_name not in spotify_by_normalized
    ]

    primary_lyric_tracks = spotify_snapshot.get("primary_lyric_tracks")
    if not primary_lyric_tracks:
        primary_lyric_tracks = [
            track
            for track in spotify_tracks
            if not is_redundant_variant_title(track["name"], set(spotify_by_normalized))
        ]

    primary_lyric_missing = [
        track
        for track in primary_lyric_tracks
        if track["normalized_name"] not in lyric_by_normalized
    ]
    variant_only_missing = [
        track
        for track in strict_missing_from_lyrics
        if is_redundant_variant_title(track["name"], set(spotify_by_normalized))
        and any(base_title in lyric_by_normalized for base_title in candidate_base_titles(track["name"])[1:])
    ]

    return {
        "lyric_track_count": len(lyric_tracks),
        "spotify_canonical_track_count": len(spotify_tracks),
        "spotify_primary_lyric_track_count": len(primary_lyric_tracks),
        "spotify_redundant_variant_track_count": len(spotify_tracks) - len(primary_lyric_tracks),
        "matched_count": len(spotify_by_normalized) - len(strict_missing_from_lyrics),
        "primary_lyric_matched_count": len(primary_lyric_tracks) - len(primary_lyric_missing),
        "spotify_missing_from_lyrics": strict_missing_from_lyrics,
        "spotify_primary_missing_from_lyrics": primary_lyric_missing,
        "spotify_variant_only_missing_from_lyrics": variant_only_missing,
        "lyric_missing_from_spotify": lyric_missing_from_spotify,
    }


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
