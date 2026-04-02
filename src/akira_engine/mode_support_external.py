from __future__ import annotations

from typing import Any


def validate_mode_support_payload(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    mode_id = str(payload.get("mode_id", "")).strip()
    if not mode_id:
        issues.append("missing mode_id")

    artist_candidates = payload.get("artist_candidates")
    if not isinstance(artist_candidates, list) or not artist_candidates:
        issues.append("artist_candidates must be a non-empty list")
        return issues

    for index, item in enumerate(artist_candidates, start=1):
        if not isinstance(item, dict):
            issues.append(f"artist_candidates[{index}] must be an object")
            continue
        artist_id = str(item.get("artist_id", "")).strip()
        if not artist_id:
            issues.append(f"artist_candidates[{index}] missing artist_id")
        candidate_track_ids = item.get("candidate_track_ids")
        if not isinstance(candidate_track_ids, list) or not candidate_track_ids:
            issues.append(f"artist_candidates[{index}] candidate_track_ids must be a non-empty list")
        candidate_titles = item.get("candidate_titles")
        if not isinstance(candidate_titles, list) or not candidate_titles:
            issues.append(f"artist_candidates[{index}] candidate_titles must be a non-empty list")
    return issues
