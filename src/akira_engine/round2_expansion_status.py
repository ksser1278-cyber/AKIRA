from __future__ import annotations

from pathlib import Path
from typing import Any

from .round2_expansion import load_json


def build_round2_status(project_root: Path) -> dict[str, Any]:
    registry_path = project_root / "data" / "_global" / "round2_expansion" / "registry.json"
    registry = load_json(registry_path)
    artists = registry.get("artists", [])
    enriched_artists: list[dict[str, Any]] = []
    total_scaffolded = 0
    total_candidate_only = 0
    total_completed = 0
    for artist in artists:
        artist_id = str(artist.get("artist_id", "")).strip()
        queue_path = project_root / "data" / artist_id / "reference_tracks" / "round2_queue.json"
        audit_path = project_root / "reports" / "quality" / "round2_expansion_audit" / f"{artist_id}_round2_audit.json"
        scaffolded_count = 0
        candidate_only_count = 0
        gold_count = 0
        usable_count = 0
        weak_count = 0
        average_score = 0.0
        if queue_path.exists():
            queue_payload = load_json(queue_path)
            for item in queue_payload.get("queue", []):
                status = str(item.get("status", "")).strip()
                if status == "scaffolded":
                    scaffolded_count += 1
                if status == "candidate_only":
                    candidate_only_count += 1
        if audit_path.exists():
            audit_payload = load_json(audit_path)
            gold_count = int(audit_payload.get("gold_count", 0))
            usable_count = int(audit_payload.get("usable_count", 0))
            weak_count = int(audit_payload.get("weak_count", 0))
            average_score = float(audit_payload.get("average_score", 0.0))
        completed_count = gold_count + usable_count
        total_scaffolded += scaffolded_count
        total_candidate_only += candidate_only_count
        total_completed += completed_count
        enriched = dict(artist)
        enriched["scaffolded_count"] = scaffolded_count
        enriched["candidate_only_count"] = candidate_only_count
        enriched["completed_count"] = completed_count
        enriched["gold_count"] = gold_count
        enriched["usable_count"] = usable_count
        enriched["weak_count"] = weak_count
        enriched["average_score"] = average_score
        enriched_artists.append(enriched)
    return {
        "registry_path": str(registry_path),
        "candidate_count": int(registry.get("candidate_count", 0) or 0),
        "seed_count": int(registry.get("seed_count", 0) or 0),
        "artist_count": len(artists),
        "scaffolded_count": total_scaffolded,
        "candidate_only_count": total_candidate_only,
        "completed_count": total_completed,
        "artists": enriched_artists,
    }


def render_round2_status_markdown(status: dict[str, Any]) -> str:
    lines = [
        "# Round2 Expansion Status",
        "",
        f"- candidates `{status['candidate_count']}`",
        f"- seeded `{status['seed_count']}`",
        f"- scaffolded `{status['scaffolded_count']}`",
        f"- candidate only `{status['candidate_only_count']}`",
        f"- completed `{status['completed_count']}`",
        f"- artists `{status['artist_count']}`",
        "",
    ]
    for artist in status.get("artists", []):
        lines.append(f"## {artist['artist_id']}")
        lines.append("")
        lines.append(f"- candidates `{artist['candidate_count']}`")
        lines.append(f"- seeded `{artist['seeded_count']}`")
        lines.append(f"- scaffolded `{artist['scaffolded_count']}`")
        lines.append(f"- candidate only `{artist['candidate_only_count']}`")
        lines.append(f"- completed `{artist['completed_count']}` / gold `{artist['gold_count']}` / usable `{artist['usable_count']}` / weak `{artist['weak_count']}`")
        lines.append(f"- high priority `{artist['high_priority_count']}`")
        lines.append(f"- tracks: {', '.join(artist.get('track_ids', []))}")
        lines.append("")
    return "\n".join(lines)
