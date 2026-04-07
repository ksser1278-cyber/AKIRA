from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .training_data import write_json
from .web_scrape import (
    build_requests_session,
    extract_lyrics_from_html,
    fetch_html,
    normalize_scraped_text,
)


DEFAULT_SOURCE_LABEL = "UtaTen lyrics page"
DEFAULT_SOURCE_TYPE = "trusted_lyric_db"
DEFAULT_USER_AGENT = "AKIRA-ENGINE/1.0 vocadb-lyric-grounding-auto"


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _detect_hook_lines(lines: list[str], title: str) -> list[str]:
    repeated: dict[str, int] = {}
    for line in lines:
        repeated[line] = repeated.get(line, 0) + 1
    candidates = [line for line, count in repeated.items() if count >= 2]
    if candidates:
        return candidates[:2]
    if title:
        title_hits = [line for line in lines if title in line]
        if title_hits:
            return title_hits[:2]
    by_length = sorted(lines, key=len, reverse=True)
    return by_length[:2] if by_length else []


def _single_section_map(lines: list[str], title: str) -> dict[str, Any]:
    return {
        "sections": [
            {
                "section": "full_lyric",
                "line_count": len(lines),
                "text_indices": [0, len(lines)]
            }
        ],
        "hook_lines": _detect_hook_lines(lines, title),
    }


def auto_ground_vocadb_workspace_from_url_map(
    *,
    workspace_root: Path,
    url_map: dict[str, dict[str, Any]],
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    incoming_dir = workspace_root / "incoming"
    accepted_dir = workspace_root / "accepted"
    lyric_assets_dir = workspace_root / "lyric_assets"
    section_maps_dir = workspace_root / "section_maps"
    accepted_dir.mkdir(parents=True, exist_ok=True)
    lyric_assets_dir.mkdir(parents=True, exist_ok=True)
    section_maps_dir.mkdir(parents=True, exist_ok=True)

    session = build_requests_session(DEFAULT_USER_AGENT)
    grounded: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for track_id, config in sorted(url_map.items()):
        record_path = incoming_dir / f"{track_id}.json"
        if not record_path.exists():
            skipped.append({"track_id": track_id, "reason": "missing_incoming_record"})
            continue

        record = _load_json(record_path)
        lyric_url = _safe_text(config.get("lyric_url"))
        if not lyric_url:
            skipped.append({"track_id": track_id, "reason": "missing_lyric_url"})
            continue

        try:
            html = fetch_html(session, lyric_url, timeout_seconds)
            lyrics_text, extraction_mode = extract_lyrics_from_html(
                html,
                {
                    "url": lyric_url,
                    "site_preset": config.get("site_preset", "utaten"),
                    "extraction_mode": config.get("extraction_mode", "auto"),
                },
            )
        except Exception as exc:
            skipped.append({"track_id": track_id, "reason": f"scrape_failed:{type(exc).__name__}"})
            continue

        lyric_lines = [line.strip() for line in normalize_scraped_text(lyrics_text).splitlines() if line.strip()]
        if not lyric_lines:
            skipped.append({"track_id": track_id, "reason": "empty_scraped_lyrics"})
            continue

        title = _safe_text(record.get("track_identity", {}).get("title"))
        lyric_asset_path = lyric_assets_dir / f"{track_id}.txt"
        section_map_path = section_maps_dir / f"{track_id}.sections.json"
        lyric_asset_path.write_text("\n".join(lyric_lines) + "\n", encoding="utf-8")
        write_json(section_map_path, _single_section_map(lyric_lines, title))

        if "grounding_sources" not in record:
            record["grounding_sources"] = {}
        
        lyric_sources = list(record["grounding_sources"].get("lyric_sources", []))
        lyric_sources.append(
            {
                "label": _safe_text(config.get("label")) or DEFAULT_SOURCE_LABEL,
                "source_type": _safe_text(config.get("source_type")) or DEFAULT_SOURCE_TYPE,
                "url": lyric_url,
                "notes": (
                    _safe_text(config.get("notes"))
                    or f"Auto-grounded from trusted lyric database via {extraction_mode} extraction."
                ),
            }
        )
        official_uploads = list(record["grounding_sources"].get("official_uploads", []))
        if _safe_text(config.get("official_upload")) and _safe_text(config.get("official_upload")) not in official_uploads:
            official_uploads.append(_safe_text(config.get("official_upload")))

        record["grounding_sources"]["lyric_sources"] = lyric_sources
        record["grounding_sources"]["official_uploads"] = official_uploads
        record["grounding_review"] = {
            "grounding_status": "accepted",
            "review_notes": "Auto-grounded from mapped trusted lyric source and converted into stable workspace assets.",
        }

        accepted_path = accepted_dir / record_path.name
        write_json(accepted_path, record)
        record_path.unlink()
        grounded.append(
            {
                "track_id": track_id,
                "accepted_record_path": str(accepted_path),
                "lyric_asset_path": str(lyric_asset_path),
                "section_map_path": str(section_map_path),
                "lyric_url": lyric_url,
            }
        )

    manifest = {
        "schema_version": "1.0",
        "record_type": "vocadb_lyric_grounding_auto_manifest",
        "workspace_root": str(workspace_root),
        "counts": {
            "grounded": len(grounded),
            "skipped": len(skipped),
        },
        "grounded": grounded,
        "skipped": skipped,
    }
    manifest_path = write_json(workspace_root / "vocadb_lyric_grounding_auto_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
