from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_invalid_queue(root: Path | None = None) -> dict[str, Any]:
    root = root or project_root()
    pilot_path = root / "reports" / "planning" / "generation_safety_pilot_status.json"
    payload = load_json(pilot_path)

    queue_items: list[dict[str, Any]] = []
    for artist in payload.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        for track in artist.get("tracks", []):
            if str(track.get("verdict", "")).strip() != "invalid":
                continue
            blockers = [str(blocker).strip() for blocker in track.get("blockers", []) if str(blocker).strip()]
            next_actions: list[str] = []
            if "missing_provenance" in blockers:
                next_actions.append("add lyric_sources and metadata_sources with trusted statuses")
            if "partial_grounding" in blockers:
                next_actions.append("replace compact or chorus-only grounding with section-complete lyric grounding")
            if "mode_fit_unverified" in blockers:
                next_actions.append("verify mode alignment against current mode_support taxonomy")
            if "renderer_policy_block" in blockers:
                next_actions.append("keep ready_for_prompting disabled until provenance and grounding are restored")
            if not next_actions:
                next_actions.append("review invalid record manually")

            queue_items.append(
                {
                    "artist_id": artist_id,
                    "track_id": str(track.get("track_id", "")).strip(),
                    "score": float(track.get("score", 0.0)),
                    "blockers": blockers,
                    "path": str(track.get("path", "")).strip(),
                    "remediation_status": "open",
                    "owner": "",
                    "external_evidence_required": True,
                    "auto_fix_candidate": False,
                    "next_action": next_actions[0],
                    "next_actions": next_actions,
                }
            )

    return {
        "schema_version": "1.0",
        "record_type": "generation_safety_invalid_queue",
        "invalid_count": len(queue_items),
        "artists": sorted({item["artist_id"] for item in queue_items}),
        "items": sorted(
            queue_items,
            key=lambda item: (
                item["artist_id"],
                float(item["score"]),
                item["track_id"],
            ),
        ),
    }


def render_invalid_queue_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Generation Safety Invalid Queue",
        "",
        f"- invalid records `{payload.get('invalid_count', 0)}`",
        f"- artists `{len(payload.get('artists', []))}`",
        "",
    ]
    items = payload.get("items", [])
    by_artist: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        by_artist.setdefault(str(item.get("artist_id", "")).strip(), []).append(item)

    for artist_id in sorted(by_artist):
        lines.append(f"## {artist_id}")
        lines.append("")
        for item in by_artist[artist_id]:
            blockers = ", ".join(item.get("blockers", [])) or "none"
            lines.append(
                f"- `{item['track_id']}` / score `{item['score']}` / blockers `{blockers}` / next `{item['next_action']}` / status `{item['remediation_status']}`"
            )
        lines.append("")
    return "\n".join(lines)
