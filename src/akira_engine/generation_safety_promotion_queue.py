from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _target_path(root: Path, artist_id: str, track_id: str) -> Path:
    prefix = f"{artist_id}_"
    suffix = track_id[len(prefix) :] if track_id.startswith(prefix) else track_id
    return root / "data" / artist_id / "reference_tracks" / f"{suffix}.conditioning.json"


def classify_audit_only_track(track: dict[str, Any]) -> dict[str, Any]:
    blockers = [str(blocker).strip() for blocker in track.get("blockers", []) if str(blocker).strip()]
    score = float(track.get("score", 0.0))
    blocker_set = set(blockers)

    promotion_class = "manual_review"
    recommended_next_action = "review blockers manually"
    external_evidence_required = True
    internal_review_candidate = False
    priority = "medium"

    if blocker_set == {"mode_fit_unverified"}:
        promotion_class = "mode_verification_only"
        recommended_next_action = "verify mode alignment against current taxonomy and rerun pilot"
        external_evidence_required = False
        internal_review_candidate = True
        priority = "high" if score >= 0.9 else "medium"
    elif blocker_set <= {"missing_provenance", "mode_fit_unverified"}:
        promotion_class = "metadata_backfill"
        recommended_next_action = "add trusted metadata or lyric provenance and verify mode alignment"
        external_evidence_required = True
        internal_review_candidate = True
        priority = "high" if score >= 0.75 else "medium"
    elif "partial_grounding" in blocker_set and "surface_noise_risk" in blocker_set:
        promotion_class = "grounding_and_surface_upgrade"
        recommended_next_action = "replace partial grounding with section-complete grounding and clean surface noise"
        external_evidence_required = True
        priority = "medium"
    elif "partial_grounding" in blocker_set:
        promotion_class = "grounding_upgrade"
        recommended_next_action = "replace compact or incomplete grounding with section-complete grounding"
        external_evidence_required = True
        priority = "medium"

    return {
        "score": score,
        "blockers": blockers,
        "promotion_class": promotion_class,
        "recommended_next_action": recommended_next_action,
        "external_evidence_required": external_evidence_required,
        "internal_review_candidate": internal_review_candidate,
        "priority": priority,
        "target_verdict": "planner_safe",
    }


def build_promotion_queue(root: Path | None = None) -> dict[str, Any]:
    root = root or project_root()
    pilot_path = root / "reports" / "planning" / "generation_safety_pilot_status.json"
    pilot = load_json(pilot_path)

    items: list[dict[str, Any]] = []
    class_counter: Counter[str] = Counter()
    for artist in pilot.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        for track in artist.get("tracks", []):
            if str(track.get("verdict", "")).strip() != "audit_only":
                continue
            classification = classify_audit_only_track(track)
            class_counter[classification["promotion_class"]] += 1
            items.append(
                {
                    "artist_id": artist_id,
                    "track_id": str(track.get("track_id", "")).strip(),
                    "path": str(_target_path(root, artist_id, str(track.get("track_id", "")).strip())),
                    **classification,
                    "promotion_status": "open",
                    "owner": "",
                }
            )

    items = sorted(
        items,
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}.get(item["priority"], 9),
            -float(item["score"]),
            item["artist_id"],
            item["track_id"],
        ),
    )

    return {
        "schema_version": "1.0",
        "record_type": "generation_safety_promotion_queue",
        "audit_only_count": len(items),
        "class_counts": dict(class_counter),
        "items": items,
    }


def render_promotion_queue_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Generation Safety Promotion Queue",
        "",
        f"- audit_only records `{payload.get('audit_only_count', 0)}`",
        "",
        "## Class Counts",
        "",
    ]
    class_counts = payload.get("class_counts", {})
    if class_counts:
        for key in sorted(class_counts):
            lines.append(f"- `{key}` / `{class_counts[key]}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Open Items", ""])
    for item in payload.get("items", []):
        blockers = ", ".join(item.get("blockers", [])) or "none"
        lines.append(
            f"- `{item['artist_id']}` / `{item['track_id']}` / `{item['priority']}` / `{item['promotion_class']}` / score `{item['score']}` / blockers `{blockers}` / next `{item['recommended_next_action']}`"
        )
    if not payload.get("items"):
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)
