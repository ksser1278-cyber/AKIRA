from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


PROFILE_FIELDS = (
    "genre_anchors",
    "tempo_feels",
    "groove_anchors",
    "vocal_tones",
    "vocal_behaviors",
    "production_palette",
    "arrangement_moves",
    "energy_arcs",
    "exclude_terms",
)

DEFAULT_LIMITS = {
    "genre_anchors": 4,
    "tempo_feels": 4,
    "groove_anchors": 4,
    "vocal_tones": 4,
    "vocal_behaviors": 6,
    "production_palette": 6,
    "arrangement_moves": 5,
    "energy_arcs": 4,
    "exclude_terms": 6,
}

MODE_HINTS = {
    "intimate_confessional": [
        "self-loathing",
        "vulnerability",
        "cynicism",
        "medical",
        "diagnosis",
        "fragile",
        "whisper",
        "blues",
        "monster",
        "bitter",
        "confessional",
    ],
    "night_drive": [
        "dance",
        "festival",
        "zombie",
        "bounce",
        "edm",
        "jumpstyle",
        "club",
        "party",
        "showtime",
        "blackout",
        "electro",
        "night",
    ],
    "anthemic_cinematic": [
        "heroism",
        "heroic",
        "liberation",
        "anthem",
        "anthemic",
        "cinematic",
        "orchestral",
        "rock",
        "apocalyptic",
        "future",
        "defiance",
        "rebellion",
        "radiant",
        "epic",
    ],
}

MODE_TIE_BREAK = ("night_drive", "intimate_confessional", "anthemic_cinematic")

GROOVE_HINT_TOKENS = (
    "pulse",
    "groove",
    "swing",
    "bounce",
    "motion",
    "downbeat",
    "syncop",
    "march",
    "stomp",
    "straight",
    "push",
    "drive",
)

MODE_DEFAULTS = {
    "intimate_confessional": {
        "default_theme_axes": ["body", "noise", "darkness"],
        "default_form_tags": ["extended_lead_in", "bridge_lift", "tag_outro"],
        "default_arc_label": "steady_build_to_final_release",
    },
    "night_drive": {
        "default_theme_axes": ["night", "city", "motion"],
        "default_form_tags": ["chorus_open", "interlude_break", "multi_wave_hooking"],
        "default_arc_label": "steady_build_to_final_release",
    },
    "anthemic_cinematic": {
        "default_theme_axes": ["uplift", "motion", "weather"],
        "default_form_tags": ["bridge_lift", "multi_wave_hooking", "tag_outro"],
        "default_arc_label": "steady_build_to_final_release",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def clean_text(value: Any) -> str:
    return " ".join(str(value).strip().split())


def unique(items: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = clean_text(item)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            output.append(cleaned)
    return output


def load_conditioning_records(reference_dir: Path) -> list[dict[str, Any]]:
    records = [load_json(path) for path in sorted(reference_dir.glob("*.conditioning.json"))]
    return sorted(records, key=lambda record: record["track_identity"]["track_id"])


def text_blob_for_mode(record: dict[str, Any]) -> str:
    parts: list[str] = []
    song_intent = record.get("song_intent", {})
    prompt_conditioning = record.get("prompt_conditioning", {})
    audio_proxy = record.get("audio_fact_layer", {}).get("proxy_inference", {})
    for key in (
        "core_theme",
        "contrast_device",
        "dramatic_arc",
        "key_motifs",
    ):
        parts.extend(song_intent.get(key, []))
    parts.append(song_intent.get("emotional_thesis", ""))
    parts.append(song_intent.get("title_function", ""))
    for key in (
        "genre_anchors",
        "tempo_feels",
        "vocal_tones",
        "production_palette",
        "imagery_anchors",
        "exclude",
    ):
        parts.extend(prompt_conditioning.get(key, []))
    for key in (
        "energy_profile",
        "vocal_behavior",
        "production_palette",
        "arrangement_arc",
        "dynamics_arc",
    ):
        parts.extend(audio_proxy.get(key, []))
    tie_in = record.get("track_identity", {}).get("tie_in", {})
    parts.append(tie_in.get("media_type", ""))
    parts.append(tie_in.get("role_label", ""))
    return " ".join(clean_text(part).lower() for part in parts if clean_text(part))


def infer_mode(record: dict[str, Any]) -> tuple[str, list[str]]:
    blob = text_blob_for_mode(record)
    scores: Counter[str] = Counter()
    reasons: dict[str, list[str]] = defaultdict(list)
    for mode_id, hints in MODE_HINTS.items():
        for hint in hints:
            if hint in blob:
                scores[mode_id] += 1
                if hint not in reasons[mode_id]:
                    reasons[mode_id].append(hint)

    tie_in = record.get("track_identity", {}).get("tie_in", {})
    media_type = clean_text(tie_in.get("media_type", "")).lower()
    if media_type == "drama":
        scores["intimate_confessional"] += 1
        reasons["intimate_confessional"].append("drama_tie_in")
    elif media_type in {"event", "tv_program"}:
        scores["night_drive"] += 1
        reasons["night_drive"].append(media_type)
    elif media_type == "film":
        scores["anthemic_cinematic"] += 1
        reasons["anthemic_cinematic"].append("film_tie_in")

    if not scores:
        return "anthemic_cinematic", []

    top_score = max(scores.values())
    winners = [mode_id for mode_id, score in scores.items() if score == top_score]
    for mode_id in MODE_TIE_BREAK:
        if mode_id in winners:
            return mode_id, unique(reasons.get(mode_id, []))[:5]
    return winners[0], unique(reasons.get(winners[0], []))[:5]


def extract_field_values(record: dict[str, Any], field_name: str) -> list[str]:
    prompt_conditioning = record.get("prompt_conditioning", {})
    audio_proxy = record.get("audio_fact_layer", {}).get("proxy_inference", {})
    section_analysis = record.get("section_analysis", [])

    if field_name in {"genre_anchors", "tempo_feels", "vocal_tones"}:
        return unique(prompt_conditioning.get(field_name, []))
    if field_name == "vocal_behaviors":
        return unique(audio_proxy.get("vocal_behavior", []))
    if field_name == "production_palette":
        return unique(
            list(prompt_conditioning.get("production_palette", []))
            + list(audio_proxy.get("production_palette", []))
        )
    if field_name == "arrangement_moves":
        return unique(audio_proxy.get("arrangement_arc", []))
    if field_name == "energy_arcs":
        return unique(
            list(prompt_conditioning.get("energy_arc", []))
            + list(audio_proxy.get("dynamics_arc", []))
        )
    if field_name == "exclude_terms":
        return unique(prompt_conditioning.get("exclude", []))
    if field_name == "groove_anchors":
        candidates: list[str] = []
        for section in section_analysis:
            candidates.extend(section.get("rhythm_features", []))
        candidates.extend(audio_proxy.get("energy_profile", []))
        candidates.extend(prompt_conditioning.get("tempo_feels", []))
        filtered = [
            candidate
            for candidate in unique(candidates)
            if any(token in candidate.lower() for token in GROOVE_HINT_TOKENS)
        ]
        return filtered or unique(candidates)[:4]
    return []


def aggregate_field(
    records: list[dict[str, Any]],
    field_name: str,
    *,
    fallback: list[str] | None = None,
    limit: int,
) -> tuple[list[str], list[dict[str, Any]]]:
    fallback = fallback or []
    counts: Counter[str] = Counter()
    order: list[str] = []
    tracks_for_value: dict[str, list[str]] = defaultdict(list)
    titles_for_value: dict[str, list[str]] = defaultdict(list)

    for record in records:
        track_id = record["track_identity"]["track_id"]
        title_core = record["track_identity"].get("title_core") or record["track_identity"]["title"]
        for value in extract_field_values(record, field_name):
            if value not in counts:
                order.append(value)
            counts[value] += 1
            if track_id not in tracks_for_value[value]:
                tracks_for_value[value].append(track_id)
            if title_core not in titles_for_value[value]:
                titles_for_value[value].append(title_core)

    sorted_values = sorted(counts, key=lambda value: (-counts[value], order.index(value)))
    merged = unique(sorted_values + fallback)[:limit]
    evidence = [
        {
            "value": value,
            "count": counts[value],
            "track_ids": tracks_for_value[value],
            "titles": titles_for_value[value],
        }
        for value in merged
        if value in counts
    ]
    return merged, evidence


def aggregate_atom_block(
    records: list[dict[str, Any]],
    *,
    fallback_block: dict[str, Any] | None = None,
) -> tuple[dict[str, list[str]], dict[str, list[dict[str, Any]]]]:
    fallback_block = fallback_block or {}
    block: dict[str, list[str]] = {}
    evidence: dict[str, list[dict[str, Any]]] = {}
    for field_name in PROFILE_FIELDS:
        fallback_values = list(fallback_block.get(field_name, []))
        limit = max(DEFAULT_LIMITS[field_name], len(fallback_values))
        values, field_evidence = aggregate_field(
            records,
            field_name,
            fallback=fallback_values,
            limit=limit,
        )
        block[field_name] = values
        evidence[field_name] = field_evidence
    return block, evidence


def mode_defaults(mode_id: str, base_mode: dict[str, Any]) -> dict[str, Any]:
    defaults = dict(MODE_DEFAULTS.get(mode_id, {}))
    return {
        "default_theme_axes": list(base_mode.get("default_theme_axes", defaults.get("default_theme_axes", []))),
        "default_form_tags": list(base_mode.get("default_form_tags", defaults.get("default_form_tags", []))),
        "default_arc_label": base_mode.get("default_arc_label", defaults.get("default_arc_label", "steady_build_to_final_release")),
    }


def mode_distribution(assignments: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(item["mode_id"] for item in assignments)
    return dict(counter)


def build_generated_style_profile(
    *,
    artist_id: str,
    display_name: str,
    records: list[dict[str, Any]],
    base_profile: dict[str, Any] | None,
    reference_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    base_profile = base_profile or {}
    assignments: list[dict[str, Any]] = []
    grouped_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        mode_id, reason_tags = infer_mode(record)
        grouped_records[mode_id].append(record)
        assignments.append(
            {
                "track_id": record["track_identity"]["track_id"],
                "title_core": record["track_identity"].get("title_core") or record["track_identity"]["title"],
                "mode_id": mode_id,
                "reason_tags": reason_tags,
            }
        )

    global_atoms, global_evidence = aggregate_atom_block(
        records,
        fallback_block=dict(base_profile.get("global_atoms", {})),
    )

    mode_atoms: dict[str, Any] = {}
    mode_evidence: dict[str, Any] = {}
    base_modes = dict(base_profile.get("mode_atoms", {}))
    for mode_id in unique(list(base_modes.keys()) + list(grouped_records.keys())):
        fallback_mode = dict(base_modes.get(mode_id, {}))
        mode_block, field_evidence = aggregate_atom_block(
            grouped_records.get(mode_id, []),
            fallback_block=fallback_mode,
        )
        defaults = mode_defaults(mode_id, fallback_mode)
        mode_atoms[mode_id] = {
            **mode_block,
            **defaults,
            "evidence_track_ids": [record["track_identity"]["track_id"] for record in grouped_records.get(mode_id, [])],
            "evidence_titles": [
                record["track_identity"].get("title_core") or record["track_identity"]["title"]
                for record in grouped_records.get(mode_id, [])
            ],
        }
        mode_evidence[mode_id] = field_evidence

    generated_profile = {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "display_name": display_name,
        "reference_notes": list(base_profile.get("reference_notes", []))
        + [f"Generated from {len(records)} validated conditioning records."],
        "generated_from_conditioning": {
            "generated_on": date.today().isoformat(),
            "reference_record_dir": str(reference_dir),
            "record_count": len(records),
            "mode_distribution": mode_distribution(assignments),
            "track_mode_assignments": assignments,
        },
        "global_atoms": global_atoms,
        "axis_atoms": dict(base_profile.get("axis_atoms", {})),
        "mode_atoms": mode_atoms,
    }

    evidence = {
        "assignments": assignments,
        "global": global_evidence,
        "mode": mode_evidence,
    }
    return generated_profile, evidence


def render_evidence_report(
    *,
    generated_profile: dict[str, Any],
    evidence: dict[str, Any],
) -> str:
    generated_meta = generated_profile["generated_from_conditioning"]
    lines = [
        f"# Conditioning Style Profile: {generated_profile['display_name']}",
        "",
        f"- Record count: `{generated_meta['record_count']}`",
        f"- Mode distribution: `{generated_meta['mode_distribution']}`",
        f"- Axis atoms: `copied from base style prompt profile`",
        "",
        "## Track Assignments",
        "",
    ]
    for assignment in evidence["assignments"]:
        reason_text = ", ".join(assignment["reason_tags"]) if assignment["reason_tags"] else "fallback/default"
        lines.append(
            f"- `{assignment['track_id']}` / `{assignment['title_core']}` -> "
            f"`{assignment['mode_id']}` ({reason_text})"
        )

    lines.extend(
        [
            "",
            "## Global Atom Leaders",
            "",
        ]
    )
    for field_name in PROFILE_FIELDS:
        leaders = evidence["global"].get(field_name, [])
        if not leaders:
            continue
        label = field_name.replace("_", " ")
        summary = ", ".join(f"{item['value']} ({item['count']})" for item in leaders[:5])
        lines.append(f"- `{label}`: {summary}")

    for mode_id, mode_block in generated_profile.get("mode_atoms", {}).items():
        lines.extend(
            [
                "",
                f"## {mode_id}",
                "",
                f"- Evidence tracks: `{mode_block.get('evidence_track_ids', [])}`",
                f"- Genre anchors: `{mode_block.get('genre_anchors', [])}`",
                f"- Tempo feels: `{mode_block.get('tempo_feels', [])}`",
                f"- Groove anchors: `{mode_block.get('groove_anchors', [])}`",
                f"- Vocal tones: `{mode_block.get('vocal_tones', [])}`",
                f"- Production palette: `{mode_block.get('production_palette', [])}`",
                f"- Arrangement moves: `{mode_block.get('arrangement_moves', [])}`",
                f"- Energy arcs: `{mode_block.get('energy_arcs', [])}`",
                f"- Exclude terms: `{mode_block.get('exclude_terms', [])}`",
            ]
        )

    return "\n".join(lines) + "\n"


def build_conditioning_style_profile(
    *,
    project_root: Path,
    artist_id: str,
    reference_root: Path,
    output_profile_path: Path,
    report_root: Path,
) -> dict[str, Any]:
    reference_dir = reference_root / artist_id
    if not reference_dir.exists():
        raise FileNotFoundError(f"Reference track directory not found: {reference_dir}")

    records = load_conditioning_records(reference_dir)
    if not records:
        raise ValueError(f"No conditioning records found in: {reference_dir}")

    base_profile_path = project_root / "artists" / artist_id / "style_prompt_profile.json"
    base_profile = load_json(base_profile_path) if base_profile_path.exists() else {}
    display_name = base_profile.get("display_name") or records[0]["track_identity"]["artist_name"]

    generated_profile, evidence = build_generated_style_profile(
        artist_id=artist_id,
        display_name=display_name,
        records=records,
        base_profile=base_profile,
        reference_dir=reference_dir,
    )

    output_profile_path = output_profile_path.resolve()
    report_path = (report_root / f"{artist_id}_conditioning_style_profile.md").resolve()
    write_json(output_profile_path, generated_profile)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        render_evidence_report(generated_profile=generated_profile, evidence=evidence),
        encoding="utf-8",
    )

    return {
        "artist_id": artist_id,
        "reference_record_count": len(records),
        "generated_profile_path": str(output_profile_path),
        "report_path": str(report_path),
        "mode_distribution": generated_profile["generated_from_conditioning"]["mode_distribution"],
    }
