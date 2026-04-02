from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_promotion_handoff(root: Path | None = None) -> dict[str, Any]:
    root = root or project_root()
    queue_path = root / "reports" / "planning" / "generation_safety_promotion_queue.json"
    queue = load_json(queue_path)
    items = [
        item
        for item in queue.get("items", [])
        if str(item.get("promotion_class", "")).strip() == "metadata_backfill"
        and str(item.get("priority", "")).strip() == "high"
    ]
    by_artist: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        by_artist.setdefault(str(item.get("artist_id", "")).strip(), []).append(item)

    artists = []
    for artist_id, artist_items in sorted(by_artist.items()):
        artists.append(
            {
                "artist_id": artist_id,
                "track_count": len(artist_items),
                "tracks": sorted(
                    artist_items,
                    key=lambda item: (-float(item.get("score", 0.0)), str(item.get("track_id", ""))),
                ),
            }
        )

    return {
        "schema_version": "1.0",
        "record_type": "generation_safety_promotion_handoff",
        "selected_count": len(items),
        "artist_count": len(artists),
        "artists": artists,
    }


def render_promotion_handoff_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Generation Safety Promotion Handoff",
        "",
        f"- selected records `{payload.get('selected_count', 0)}`",
        f"- artists `{payload.get('artist_count', 0)}`",
        "",
        "## Scope",
        "",
        "- only high-priority `metadata_backfill` records are included",
        "- goal: move records from `audit_only` to `planner_safe`",
        "- do not rewrite lyric structure unless provenance verification forces a factual correction",
        "",
        "## Required Upgrades",
        "",
        "- add trusted `lyric_sources` and `metadata_sources`",
        "- verify `song_intent.narrative_role` against current supported modes",
        "- keep `ready_for_prompting` unchanged unless source verification reveals a contradiction",
        "",
    ]
    for artist in payload.get("artists", []):
        lines.append(f"## {artist['artist_id']}")
        lines.append("")
        for track in artist.get("tracks", []):
            blockers = ", ".join(track.get("blockers", [])) or "none"
            lines.append(
                f"- `{track['track_id']}` / score `{track['score']}` / blockers `{blockers}` / path `{track['path']}`"
            )
        lines.append("")
    return "\n".join(lines)


def render_promotion_batch_prompt(payload: dict[str, Any]) -> str:
    lines = [
        "This task is generation_safety promotion batch 1.",
        "",
        "Goal:",
        "- Upgrade 4 high-priority metadata_backfill records from `audit_only` toward `planner_safe` by repairing provenance and mode verification.",
        "",
        "Important:",
        "- Do not modify engine code.",
        "- Keep existing track_id values.",
        "- Submit merge-friendly JSON only.",
        "- Partial patch JSON is allowed.",
        "- Do not rewrite lyric structure.",
        "- Focus on trusted provenance and mode alignment verification.",
        "",
        "Required upgrades:",
        "- source_provenance.lyric_sources",
        "- source_provenance.metadata_sources",
        "- verify song_intent.narrative_role",
        "- extend source_provenance.notes only if needed",
        "",
        "Target files:",
    ]
    for artist in payload.get("artists", []):
        for track in artist.get("tracks", []):
            lines.append(f"- {track['path']}")
    lines.extend(
        [
            "",
            "Priority:",
            "- deco27_mozaik_role",
            "- deco27_android_girl",
            "- deco27_salamander",
            "- maretu_brain_revolution_girl",
            "",
            "Done when:",
            "- missing_provenance is cleared",
            "- mode_fit_unverified is cleared",
            "- the record can satisfy `planner_safe` conditions after provenance and verification updates",
        ]
    )
    return "\n".join(lines) + "\n"
