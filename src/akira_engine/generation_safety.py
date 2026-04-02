from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SUPPORT_ARTISTS = [
    "kanaria",
    "kairiki_bear",
    "maretu",
    "iyowa",
    "syudou",
    "neru",
]

TRUSTED_STATUSES = {"confirmed", "cross_checked"}
KNOWN_MODE_IDS = {"ironic_meta", "direct_emotional_pop", "dark_cute_breakdown"}

PLACEHOLDER_PATTERNS = [
    "scaffold",
    "placeholder",
    "awaiting full grounding",
    "initial scenario setting",
    "establishing the baseline emotion",
    "setting the thematic stage",
    "rising tension",
    "preparing the twist",
    "main title drop",
    "peak expression",
    "thematic twist",
    "vulnerable quiet moment",
    "slower or disjointed reflection",
    "maximal sonic release",
    "ending note",
    "round2 scaffold",
    "upgraded to usable via direct script structuring",
    "upgraded 32 candidate seeds",
    "full grounding required before audit promotion",
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _collect_strings(value: Any) -> list[str]:
    collected: list[str] = []
    if isinstance(value, str):
        collected.append(value)
    elif isinstance(value, list):
        for item in value:
            collected.extend(_collect_strings(item))
    elif isinstance(value, dict):
        for item in value.values():
            collected.extend(_collect_strings(item))
    return collected


def _track_file_from_id(root: Path, artist_id: str, track_id: str) -> Path:
    suffix = track_id
    prefix = f"{artist_id}_"
    if track_id.startswith(prefix):
        suffix = track_id[len(prefix) :]
    return root / "data" / artist_id / "reference_tracks" / f"{suffix}.conditioning.json"


def _load_round2_track_ids(root: Path) -> list[tuple[str, str]]:
    status_path = root / "reports" / "planning" / "round2_expansion_status.json"
    if not status_path.exists():
        return []
    payload = load_json(status_path)
    pairs: list[tuple[str, str]] = []
    for artist in payload.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        if not artist_id:
            continue
        for track_id in artist.get("track_ids", []):
            track_id = str(track_id).strip()
            if track_id:
                pairs.append((artist_id, track_id))
    return pairs


def target_conditioning_paths(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for artist_id, track_id in _load_round2_track_ids(root):
        candidate = _track_file_from_id(root, artist_id, track_id)
        if candidate.exists():
            paths.add(candidate)
    for artist_id in SUPPORT_ARTISTS:
        artist_dir = root / "data" / artist_id / "reference_tracks"
        if not artist_dir.exists():
            continue
        for path in artist_dir.glob("*.conditioning.json"):
            paths.add(path)
    return sorted(paths)


def _audit_index(root: Path) -> dict[str, dict[str, dict[str, Any]]]:
    index: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for artist_id in SUPPORT_ARTISTS + ["deco27", "pinocchiop"]:
        audit_path = root / "reports" / "quality" / "conditioning" / f"{artist_id}_conditioning_audit_active.json"
        if not audit_path.exists():
            continue
        payload = load_json(audit_path)
        for record in payload.get("records", []):
            track_id = str(record.get("track_id", "")).strip()
            if track_id:
                index[artist_id][track_id] = {
                    "grade": str(record.get("grade", "")).strip(),
                    "score": float(record.get("score", 0.0)),
                }
    return index


def _placeholder_hits(record: dict[str, Any]) -> list[str]:
    haystack = "\n".join(_collect_strings(record)).lower()
    return [pattern for pattern in PLACEHOLDER_PATTERNS if pattern in haystack]


def _latin_ratio(strings: list[str]) -> float:
    joined = "".join(strings)
    if not joined:
        return 0.0
    latin = sum(1 for ch in joined if ("a" <= ch.lower() <= "z"))
    return latin / max(len(joined), 1)


def _provenance_score(record: dict[str, Any]) -> float:
    provenance = record.get("source_provenance", {})
    lyric_sources = provenance.get("lyric_sources", []) or []
    metadata_sources = provenance.get("metadata_sources", []) or []
    trusted_sources = [
        item
        for item in lyric_sources + metadata_sources
        if str(item.get("status", "")).strip() in TRUSTED_STATUSES
    ]
    total_sources = len(lyric_sources) + len(metadata_sources)
    score = 0.0
    if lyric_sources:
        score += 0.3
    if metadata_sources:
        score += 0.2
    if total_sources:
        score += 0.5 * (len(trusted_sources) / total_sources)
    return round(min(score, 1.0), 2)


def _grounding_score(record: dict[str, Any]) -> float:
    lyric = record.get("lyric_ground_truth", {})
    sections = lyric.get("sections", []) or []
    hook_lines = lyric.get("hook_lines", []) or []
    analyses = record.get("section_analysis", []) or []
    quality = record.get("quality_control", {})
    status = str(lyric.get("full_text_status", "")).strip()
    score = 0.0
    if status == "full":
        score += 0.35
    elif status == "partial":
        score += 0.15
    score += min(len(sections), 5) / 5 * 0.2
    score += min(len(analyses), 5) / 5 * 0.25
    score += min(len(hook_lines), 2) / 2 * 0.1
    if bool(quality.get("ready_for_prompting", False)):
        score += 0.1
    return round(min(score, 1.0), 2)


def _surface_score(record: dict[str, Any], placeholder_hits: list[str]) -> float:
    lyric = record.get("lyric_ground_truth", {})
    strings = _collect_strings(lyric.get("sections", [])) + _collect_strings(lyric.get("hook_lines", []))
    ratio = _latin_ratio(strings)
    score = 1.0
    if placeholder_hits:
        score = 0.1
    elif ratio >= 0.2:
        score -= 0.25
    elif ratio >= 0.1:
        score -= 0.1
    return round(max(min(score, 1.0), 0.0), 2)


def _renderer_readiness(record: dict[str, Any], placeholder_hits: list[str], grounding_score: float, surface_score: float) -> float:
    if placeholder_hits:
        return 0.0
    quality = record.get("quality_control", {})
    if not bool(quality.get("ready_for_prompting", False)):
        return round(min(grounding_score, surface_score) * 0.5, 2)
    return round(min(grounding_score, surface_score), 2)


def _risk_level(score: float) -> str:
    if score >= 0.8:
        return "low"
    if score >= 0.5:
        return "medium"
    return "high"


def _declared_mode_ids(record: dict[str, Any]) -> list[str]:
    song_intent = record.get("song_intent", {}) if isinstance(record.get("song_intent", {}), dict) else {}
    narrative_role = song_intent.get("narrative_role", [])
    if not isinstance(narrative_role, list):
        return []
    return [
        value
        for value in [str(item).strip() for item in narrative_role]
        if value in KNOWN_MODE_IDS
    ]


def infer_generation_safety(record: dict[str, Any], audit_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    placeholder_hits = _placeholder_hits(record)
    provenance_score = _provenance_score(record)
    grounding_score = _grounding_score(record)
    surface_score = _surface_score(record, placeholder_hits)
    renderer_readiness = _renderer_readiness(record, placeholder_hits, grounding_score, surface_score)
    audit_grade = str((audit_meta or {}).get("grade", "")).strip().lower()
    lyric = record.get("lyric_ground_truth", {})
    provenance = record.get("source_provenance", {})
    quality = record.get("quality_control", {})
    declared_modes = _declared_mode_ids(record)
    provisional_mode_verified = (
        not audit_grade
        and len(declared_modes) == 1
        and provenance_score >= 0.7
        and grounding_score >= 0.7
        and surface_score >= 0.7
        and bool(quality.get("ready_for_prompting", False))
        and not placeholder_hits
    )

    blockers: list[str] = []
    if not (provenance.get("lyric_sources") and provenance.get("metadata_sources")):
        blockers.append("missing_provenance")
    if str(lyric.get("full_text_status", "")).strip() != "full" or placeholder_hits:
        blockers.append("partial_grounding")
    if surface_score < 0.5:
        blockers.append("surface_noise_risk")
    if audit_grade and audit_grade not in {"gold", "usable"}:
        blockers.append("mode_fit_unverified")
    if not audit_grade and not provisional_mode_verified:
        blockers.append("mode_fit_unverified")
    if not bool(quality.get("ready_for_prompting", False)):
        blockers.append("renderer_policy_block")

    blockers = list(dict.fromkeys(blockers))

    planner_allowed = (
        not placeholder_hits
        and provenance_score >= 0.5
        and grounding_score >= 0.6
        and (audit_grade in {"gold", "usable"} or provisional_mode_verified)
    )
    benchmark_allowed = (
        planner_allowed
        and provenance_score >= 0.7
        and bool(provenance.get("lyric_sources"))
        and bool(provenance.get("metadata_sources"))
        and audit_grade in {"gold", "usable"}
    )

    verdict = "audit_only"
    if benchmark_allowed:
        verdict = "benchmark_safe"
    elif planner_allowed:
        verdict = "planner_safe"
    elif provenance_score < 0.3 and grounding_score < 0.3:
        verdict = "invalid"

    score = round(
        (
            provenance_score * 0.35
            + grounding_score * 0.3
            + surface_score * 0.2
            + renderer_readiness * 0.15
        ),
        2,
    )

    return {
        "schema_version": "1.0",
        "verdict": verdict,
        "score": score,
        "score_breakdown": {
            "provenance_trust": provenance_score,
            "grounding_completeness": grounding_score,
            "surface_safety": surface_score,
            "renderer_readiness": renderer_readiness,
        },
        "allowed_layers": {
            "planner": planner_allowed,
            "renderer": False,
            "lexical_sampling": False,
            "benchmark": benchmark_allowed,
        },
        "blockers": blockers,
        "requires_human_review": verdict != "benchmark_safe",
        "risk_levels": {
            "leakage": "medium",
            "surface_contamination": _risk_level(surface_score),
            "anchor_similarity": "medium",
        },
        "notes": (
            ["pilot relabel only; renderer and lexical sampling remain disabled"]
            + ([f"placeholder indicators: {', '.join(placeholder_hits[:3])}"] if placeholder_hits else [])
        ),
    }


def apply_generation_safety_pilot(root: Path, overwrite: bool = False) -> dict[str, Any]:
    audits = _audit_index(root)
    verdict_counter: Counter[str] = Counter()
    artist_counters: dict[str, Counter[str]] = defaultdict(Counter)
    blocker_counter: Counter[str] = Counter()
    track_rows_by_artist: dict[str, list[dict[str, Any]]] = defaultdict(list)
    modified = 0
    skipped_existing = 0
    target_paths_list = target_conditioning_paths(root)

    for path in target_paths_list:
        payload = load_json(path)
        if payload.get("generation_safety") and not overwrite:
            skipped_existing += 1
            generation_safety = payload["generation_safety"]
        else:
            track_identity = payload.get("track_identity", {}) if isinstance(payload.get("track_identity", {}), dict) else {}
            artist_id = str(track_identity.get("artist_id", "") or track_identity.get("artist", "")).strip()
            track_id = str(payload.get("track_identity", {}).get("track_id", "")).strip()
            audit_meta = audits.get(artist_id, {}).get(track_id)
            generation_safety = infer_generation_safety(payload, audit_meta)
            payload["generation_safety"] = generation_safety
            save_json(path, payload)
            modified += 1

        track_identity = payload.get("track_identity", {}) if isinstance(payload.get("track_identity", {}), dict) else {}
        artist_id = str(track_identity.get("artist_id", "") or track_identity.get("artist", "")).strip() or "unknown"
        track_id = str(track_identity.get("track_id", "")).strip() or path.stem.replace(".conditioning", "")
        verdict = str(generation_safety.get("verdict", "invalid")).strip() or "invalid"
        verdict_counter[verdict] += 1
        artist_counters[artist_id][verdict] += 1
        for blocker in generation_safety.get("blockers", []):
            blocker_counter[str(blocker)] += 1
        track_rows_by_artist[artist_id].append(
            {
                "track_id": track_id,
                "verdict": verdict,
                "score": float(generation_safety.get("score", 0.0)),
                "blockers": [str(blocker) for blocker in generation_safety.get("blockers", []) if str(blocker).strip()],
                "path": str(path),
            }
        )

    artists_summary = []
    for artist_id in sorted(artist_counters):
        counts = artist_counters[artist_id]
        track_rows = sorted(
            track_rows_by_artist.get(artist_id, []),
            key=lambda item: (
                {"invalid": 0, "audit_only": 1, "planner_safe": 2, "generation_safe": 3, "benchmark_safe": 4}.get(
                    item.get("verdict", ""),
                    99,
                ),
                float(item.get("score", 0.0)),
                str(item.get("track_id", "")),
            ),
        )
        artists_summary.append(
            {
                "artist_id": artist_id,
                "record_count": sum(counts.values()),
                "invalid_count": counts.get("invalid", 0),
                "audit_only_count": counts.get("audit_only", 0),
                "planner_safe_count": counts.get("planner_safe", 0),
                "generation_safe_count": counts.get("generation_safe", 0),
                "benchmark_safe_count": counts.get("benchmark_safe", 0),
                "tracks": track_rows,
            }
        )

    return {
        "schema_version": "1.0",
        "record_type": "generation_safety_pilot_status",
        "target_record_count": len(target_paths_list),
        "modified_count": modified,
        "skipped_existing_count": skipped_existing,
        "verdict_counts": {
            "invalid": verdict_counter.get("invalid", 0),
            "audit_only": verdict_counter.get("audit_only", 0),
            "planner_safe": verdict_counter.get("planner_safe", 0),
            "generation_safe": verdict_counter.get("generation_safe", 0),
            "benchmark_safe": verdict_counter.get("benchmark_safe", 0),
        },
        "top_blockers": [
            {"blocker": blocker, "count": count}
            for blocker, count in blocker_counter.most_common(5)
        ],
        "artists": artists_summary,
        "target_paths": [str(path) for path in target_paths_list],
    }


def render_generation_safety_pilot_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Generation Safety Pilot Status",
        "",
        f"- target records `{payload.get('target_record_count', 0)}`",
        f"- modified `{payload.get('modified_count', 0)}`",
        f"- skipped existing `{payload.get('skipped_existing_count', 0)}`",
        "",
        "## Verdicts",
        "",
    ]
    verdict_counts = payload.get("verdict_counts", {})
    for key in ["invalid", "audit_only", "planner_safe", "generation_safe", "benchmark_safe"]:
        lines.append(f"- {key}: `{verdict_counts.get(key, 0)}`")
    lines.extend(["", "## Top Blockers", ""])
    blockers = payload.get("top_blockers", [])
    if blockers:
        for item in blockers:
            lines.append(f"- `{item.get('blocker', '')}` / `{item.get('count', 0)}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Artists", ""])
    for artist in payload.get("artists", []):
        lines.append(f"### {artist['artist_id']}")
        lines.append("")
        lines.append(f"- records `{artist['record_count']}`")
        lines.append(f"- invalid `{artist['invalid_count']}`")
        lines.append(f"- audit_only `{artist['audit_only_count']}`")
        lines.append(f"- planner_safe `{artist['planner_safe_count']}`")
        lines.append(f"- generation_safe `{artist['generation_safe_count']}`")
        lines.append(f"- benchmark_safe `{artist['benchmark_safe_count']}`")
        flagged_tracks = [
            item
            for item in artist.get("tracks", [])
            if str(item.get("verdict", "")).strip() in {"invalid", "audit_only"}
        ]
        planner_safe_tracks = [
            item
            for item in artist.get("tracks", [])
            if str(item.get("verdict", "")).strip() == "planner_safe"
        ]
        if flagged_tracks:
            lines.append(f"- flagged tracks `{', '.join(str(item.get('track_id', '')).strip() for item in flagged_tracks)}`")
        if planner_safe_tracks:
            lines.append(f"- planner-safe tracks `{', '.join(str(item.get('track_id', '')).strip() for item in planner_safe_tracks)}`")
        lines.append("")
    return "\n".join(lines)
