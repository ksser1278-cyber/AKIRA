"""
enrich_skeleton_wiki_tracks.py
==============================
32개 스켈레톤 Wiki 트랙에 VocaDB API에서 producer/voicebank 메타데이터를 채워 넣습니다.

VocaDB REST API: https://vocadb.net/api/songs/{id}?fields=Artists
"""
from __future__ import annotations

import re
import sys
import time
import urllib.request
import json
from pathlib import Path


def safe_print(text: str, **kwargs):
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()

WIKI_TRACKS_DIR = Path(__file__).resolve().parents[2] / "wiki" / "tracks"
VOCADB_API = "https://vocadb.net/api/songs"
USER_AGENT = "AKIRA-Engine/1.0 (metadata enrichment)"

# Size threshold for skeleton detection
SKELETON_MAX_BYTES = 600


def fetch_vocadb_song(song_id: int) -> dict | None:
    url = f"{VOCADB_API}/{song_id}?fields=Artists"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        safe_print(f"    [WARN] API error for {song_id}: {e}")
        return None


def extract_artist_info(song_data: dict) -> tuple[str, str]:
    """Returns (producer, voicebanks)."""
    producers = []
    voicebanks = []
    for artist_entry in song_data.get("artists", []):
        categories = str(artist_entry.get("categories", "")).lower()
        artist_obj = artist_entry.get("artist", {})
        name = artist_obj.get("name", "") or artist_entry.get("name", "")
        if not name:
            continue
        if "producer" in categories or "composer" in categories:
            producers.append(name)
        elif "vocalist" in categories or "vocaloid" in categories or "synthesizer" in categories:
            voicebanks.append(name)
    producer = producers[0] if producers else "unknown"
    vb = ", ".join(voicebanks) if voicebanks else "unknown"
    return producer, vb


def extract_upload_info(song_data: dict) -> tuple[str, str]:
    """Returns (platform, upload_date)."""
    publish_date = song_data.get("publishDate", "")
    create_date = song_data.get("createDate", "")
    date = publish_date or create_date or "unknown"

    pvs = song_data.get("pvs", [])
    if pvs:
        service = pvs[0].get("service", "unknown")
    else:
        service = "unknown"

    platform_map = {
        "NicoNicoDouga": "niconico",
        "Youtube": "youtube",
        "Piapro": "piapro",
        "SoundCloud": "soundcloud",
    }
    platform = platform_map.get(service, service.lower() if service != "unknown" else "unknown")
    return platform, date


def update_wiki_track(track_path: Path, song_data: dict) -> bool:
    """Updates the wiki track markdown with enriched metadata. Returns True if modified."""
    content = track_path.read_text(encoding="utf-8")
    producer, voicebanks = extract_artist_info(song_data)
    platform, upload_date = extract_upload_info(song_data)

    modified = False

    # Replace producer
    if "producer: `unknown`" in content and producer != "unknown":
        content = content.replace("producer: `unknown`", f"producer: `{producer}`")
        modified = True

    # Replace voicebanks
    if "voicebanks: `unknown`" in content and voicebanks != "unknown":
        content = content.replace("voicebanks: `unknown`", f"voicebanks: `{voicebanks}`")
        modified = True

    # Replace platform
    if "original platform: `unknown`" in content and platform != "unknown":
        content = content.replace("original platform: `unknown`", f"original platform: `{platform}`")
        modified = True

    # Replace upload date
    if "original upload date: `unknown`" in content and upload_date != "unknown":
        content = content.replace("original upload date: `unknown`", f"original upload date: `{upload_date}`")
        modified = True

    # Add VocaDB source if missing
    song_id = song_data.get("id", 0)
    vocadb_url = f"https://vocadb.net/S/{song_id}"
    if vocadb_url not in content:
        # Replace "- none" under Sources with actual source
        content = content.replace(
            "## Sources\n\n- none",
            f"## Sources\n\n- [VocaDB song {song_id}]({vocadb_url})"
        )
        # Also try with \r\n
        content = content.replace(
            "## Sources\r\n\r\n- none",
            f"## Sources\r\n\r\n- [VocaDB song {song_id}]({vocadb_url})"
        )
        modified = True

    if modified:
        track_path.write_text(content, encoding="utf-8")

    return modified


def main():
    skeleton_tracks = [
        p for p in sorted(WIKI_TRACKS_DIR.glob("vocadb_*.md"))
        if p.stat().st_size < SKELETON_MAX_BYTES
    ]

    safe_print(f"Found {len(skeleton_tracks)} skeleton tracks to enrich.")
    enriched = 0
    failed = 0

    for track_path in skeleton_tracks:
        # Extract song ID from filename: vocadb_12345.md -> 12345
        match = re.match(r"vocadb_(\d+)\.md", track_path.name)
        if not match:
            continue
        song_id = int(match.group(1))

        safe_print(f"  [{enriched + failed + 1}/{len(skeleton_tracks)}] vocadb_{song_id}...", end=" ", flush=True)

        song_data = fetch_vocadb_song(song_id)
        if not song_data:
            safe_print("FAILED (API)")
            failed += 1
            time.sleep(1)
            continue

        title = song_data.get("name", "?")
        producer, vb = extract_artist_info(song_data)

        if update_wiki_track(track_path, song_data):
            safe_print(f"OK - {title} | {producer} | {vb}")
            enriched += 1
        else:
            safe_print(f"NO CHANGE - {title}")

        # Rate limit: VocaDB asks for 1 req/sec
        time.sleep(1.0)

    safe_print(f"\nDone. Enriched: {enriched}, Failed: {failed}, Unchanged: {len(skeleton_tracks) - enriched - failed}")


if __name__ == "__main__":
    main()
