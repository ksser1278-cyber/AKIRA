from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FORM_ARRANGEMENT_HINTS = {
    "chorus_open": "immediate hook-forward opening",
    "interlude_break": "brief instrumental reset before the next lift",
    "bridge_lift": "bridge that opens into a larger final chorus",
    "bridge_turn": "bridge that changes perspective before the last chorus",
    "tag_outro": "short afterimage outro",
    "multi_wave_hooking": "multiple chorus waves instead of one flat peak",
}

ARC_FALLBACKS = {
    "build_and_drop": "build pressure in the verses and let the chorus hit with a stronger emotional drop",
    "steady_build_to_final_release": "keep rising section by section and save the clearest release for the final chorus",
    "flat_or_circular": "keep a repeating gravity in the early sections and open only a little wider at the end",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_text(value: str) -> str:
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


def limit(items: list[str], count: int) -> list[str]:
    return unique(items)[:count]


def find_project_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "artists").exists() and (candidate / "src").exists():
            return candidate
    return None


def load_style_prompt_profile(*, artist_id: str, start_path: Path, prefer_generated: bool = False) -> dict[str, Any] | None:
    project_root = find_project_root(start_path)
    if not project_root:
        return None
    artist_dir = project_root / "artists" / artist_id
    filenames = (
        ("style_prompt_profile.generated.json", "style_prompt_profile.json")
        if prefer_generated
        else ("style_prompt_profile.json", "style_prompt_profile.generated.json")
    )
    for filename in filenames:
        profile_path = artist_dir / filename
        if profile_path.exists():
            return load_json(profile_path)
    return None


def merge_atoms(primary: dict[str, Any], fallback: dict[str, Any], key: str, *, count: int) -> list[str]:
    return limit(list(primary.get(key, [])) + list(fallback.get(key, [])), count)


def resolve_style_prompt_content(*, plan: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    artist_id = str(plan.get("artist_id", "")).strip()
    prefer_generated = bool(plan.get("conditioning_context", {}).get("available"))
    profile = load_style_prompt_profile(artist_id=artist_id, start_path=run_dir, prefer_generated=prefer_generated)

    if not profile:
        return {
            "source": "fallback",
            "mode_id": str(plan.get("primary_mode", "")).strip(),
            "genre_anchors": [],
            "tempo_feels": [],
            "groove_anchors": [],
            "vocal_tones": [],
            "vocal_behaviors": [],
            "production_palette": [],
            "arrangement_moves": [],
            "energy_arc": ARC_FALLBACKS.get(str(plan.get("arc_label", "")).strip(), ""),
            "atmosphere_terms": [],
            "exclude_terms": [],
        }

    base_style_tags = [str(tag) for tag in profile.get("base_style_tags", []) if str(tag).strip()]
    is_vocaloid_profile = any(tag.lower() in {"vocaloid", "synthesized vocals", "synthetic tone", "high-pitched tuning"} for tag in base_style_tags)

    global_atoms = dict(profile.get("global_atoms", {}))
    mode_id = str(plan.get("primary_mode", "")).strip()
    mode_atoms = dict(profile.get("mode_atoms", {}).get(mode_id, {}))
    theme_axes = [str(axis) for axis in plan.get("theme_axes", []) if axis]
    form_tags = [str(tag) for tag in plan.get("form_profile", {}).get("tags", []) if tag]

    atmosphere_terms: list[str] = []
    axis_palette: list[str] = []
    axis_excludes: list[str] = []
    for axis in theme_axes:
        axis_group = dict(profile.get("axis_atoms", {}).get(axis, {}))
        atmosphere_terms.extend(axis_group.get("atmosphere_terms", []))
        axis_palette.extend(axis_group.get("production_palette", []))
        axis_excludes.extend(axis_group.get("exclude_terms", []))

    form_hints = [FORM_ARRANGEMENT_HINTS[tag] for tag in form_tags if tag in FORM_ARRANGEMENT_HINTS]
    energy_arc_candidates = list(mode_atoms.get("energy_arcs", [])) + list(global_atoms.get("energy_arcs", []))
    arc_fallback = ARC_FALLBACKS.get(str(plan.get("arc_label", "")).strip(), "")
    energy_arc = clean_text(energy_arc_candidates[0]) if energy_arc_candidates else arc_fallback

    vocaloid_vocal_behaviors = []
    vocaloid_arrangement_moves = []
    vocaloid_atmosphere = []
    vocaloid_excludes = []
    if is_vocaloid_profile:
        vocaloid_vocal_behaviors = [
            "synthetic lead articulation",
            "compressed mora phrasing",
            "machine-tight rhythmic diction",
            "digitally clipped emotional lift",
        ]
        vocaloid_arrangement_moves = [
            "vocal-synth-forward topline",
            "precise phrase-loop transitions",
            "hook sections with tighter syllable compression",
        ]
        vocaloid_atmosphere = [
            "synthetic pop pressure",
            "digitally sharpened emotional color",
        ]
        vocaloid_excludes = [
            "human belting phrasing",
            "organic singer-songwriter delivery",
            "warm live-band looseness",
        ]

    return {
        "source": "artist_style_prompt_profile",
        "profile_display_name": profile.get("display_name"),
        "mode_id": mode_id,
        "genre_anchors": merge_atoms(mode_atoms, global_atoms, "genre_anchors", count=2),
        "tempo_feels": merge_atoms(mode_atoms, global_atoms, "tempo_feels", count=2),
        "groove_anchors": merge_atoms(mode_atoms, global_atoms, "groove_anchors", count=2),
        "vocal_tones": merge_atoms(mode_atoms, global_atoms, "vocal_tones", count=2),
        "vocal_behaviors": limit(
            merge_atoms(mode_atoms, global_atoms, "vocal_behaviors", count=4) + vocaloid_vocal_behaviors,
            5,
        ),
        "production_palette": limit(
            list(mode_atoms.get("production_palette", []))
            + axis_palette
            + list(global_atoms.get("production_palette", [])),
            5,
        ),
        "arrangement_moves": limit(
            list(mode_atoms.get("arrangement_moves", []))
            + form_hints
            + vocaloid_arrangement_moves
            + list(global_atoms.get("arrangement_moves", [])),
            5,
        ),
        "energy_arc": energy_arc,
        "atmosphere_terms": limit(atmosphere_terms + vocaloid_atmosphere, 5),
        "exclude_terms": limit(
            list(mode_atoms.get("exclude_terms", []))
            + axis_excludes
            + vocaloid_excludes
            + list(global_atoms.get("exclude_terms", [])),
            10,
        ),
    }
