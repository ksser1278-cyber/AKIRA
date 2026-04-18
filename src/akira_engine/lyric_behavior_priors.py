from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

from .lyric_utils import safe_text, unique_preserve_order
from .songwriter_io import candidate_content_roots


DEFAULT_CALIBRATION_ARTISTS = ("maretu", "deco27", "pinocchiop", "kanaria")


def _top(values: list[str], limit: int = 1) -> list[str]:
    counts = Counter(value for value in values if safe_text(value))
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [value for value, _ in ordered[:limit]]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _int_band(values: list[int], *, floor_value: int = 0) -> dict[str, int]:
    clean = sorted(int(value) for value in values if int(value) >= floor_value)
    if not clean:
        return {"min": floor_value, "max": floor_value, "median": floor_value}
    mid = int(round(median(clean)))
    if len(set(clean)) == 1 and mid <= 2:
        low = mid
    else:
        low = max(floor_value, mid - 1)
    high = max(low, min(max(clean), mid + 1))
    return {"min": int(low), "max": int(high), "median": int(mid)}


def _float_band(values: list[float], *, floor_value: float = 0.0) -> dict[str, float]:
    clean = sorted(float(value) for value in values if float(value) >= floor_value)
    if not clean:
        return {"min": floor_value, "max": floor_value, "median": floor_value}
    mid = round(float(median(clean)), 2)
    low = round(max(floor_value, min(clean), mid - 2.0), 2)
    high = round(max(low, min(max(clean), mid + 2.0)), 2)
    return {"min": low, "max": high, "median": mid}


def _section_contrast_role(section_name: str) -> str:
    mapping = {
        "intro": "setup",
        "verse_1": "pressure",
        "verse_2": "escalation",
        "pre_chorus": "lift",
        "pre_chorus_2": "surge",
        "chorus": "release",
        "bridge": "break",
        "chorus_final": "climax",
        "outro": "aftermath",
    }
    return mapping.get(safe_text(section_name), "pressure")


def _closure_strength_target(section_name: str, cadence_family: str) -> str:
    clean_section = safe_text(section_name)
    clean_cadence = safe_text(cadence_family)
    if clean_section == "chorus_final":
        return "high"
    if clean_section.startswith("chorus"):
        return "high" if clean_cadence in {"compressed", "explosive"} else "medium"
    if clean_section.startswith("pre_chorus"):
        return "medium"
    if clean_section == "bridge":
        return "low"
    if clean_section == "outro":
        return "medium"
    return "low"


def _repetition_budget(
    section_name: str,
    repetition_counts: list[int],
    payoff_votes: list[str],
    hook_density_band: dict[str, int],
) -> int:
    clean_section = safe_text(section_name)
    median_repetition = int(round(median(repetition_counts))) if repetition_counts else 0
    high_payoff = sum(1 for vote in payoff_votes if safe_text(vote) == "high")
    hook_median = int(hook_density_band.get("median", 0) or 0)
    if clean_section == "chorus_final":
        return 2
    if clean_section.startswith("chorus"):
        if high_payoff > 0 or hook_median >= 2 or median_repetition >= 1:
            return 2
        return 1
    if clean_section.startswith("pre_chorus"):
        return 1 if hook_median >= 1 or median_repetition >= 1 else 0
    if clean_section == "bridge":
        return 0
    return 1 if median_repetition >= 1 else 0


def _hook_density_label(hook_density_band: dict[str, int]) -> str:
    mid = int(hook_density_band.get("median", 0) or 0)
    if mid >= 2:
        return "high"
    if mid >= 1:
        return "medium"
    return "low"


def _matching_mode_records(records: list[dict[str, Any]], mode_id: str) -> list[dict[str, Any]]:
    clean_mode = safe_text(mode_id)
    if not clean_mode:
        return records
    matched = [record for record in records if safe_text(record.get("mode_id")) == clean_mode]
    return matched or records


def summarize_behavior_priors(
    *,
    line_records: list[dict[str, Any]],
    phrase_records: list[dict[str, Any]],
    chorus_records: list[dict[str, Any]],
    mode_id: str = "",
    artist_ids: list[str] | None = None,
) -> dict[str, Any]:
    selected_artists = [safe_text(artist) for artist in (artist_ids or []) if safe_text(artist)]
    if selected_artists:
        line_records = [record for record in line_records if safe_text(record.get("artist_id")) in selected_artists]
        phrase_records = [record for record in phrase_records if safe_text(record.get("artist_id")) in selected_artists]
        chorus_records = [record for record in chorus_records if safe_text(record.get("artist_id")) in selected_artists]

    line_records = _matching_mode_records(line_records, mode_id)
    phrase_records = _matching_mode_records(phrase_records, mode_id)
    chorus_records = _matching_mode_records(chorus_records, mode_id)

    phrase_by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    chorus_by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    line_by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for record in phrase_records:
        phrase_by_section[safe_text(record.get("section_name"))].append(record)
    for record in chorus_records:
        chorus_by_section[safe_text(record.get("section_name"))].append(record)
    for record in line_records:
        line_by_section[safe_text(record.get("section_name"))].append(record)

    section_names = unique_preserve_order(
        list(phrase_by_section.keys()) + list(chorus_by_section.keys()) + list(line_by_section.keys())
    )

    section_priors: dict[str, dict[str, Any]] = {}
    for section_name in section_names:
        if not safe_text(section_name):
            continue
        phrase_items = phrase_by_section.get(section_name, [])
        chorus_items = chorus_by_section.get(section_name, [])
        line_items = line_by_section.get(section_name, [])

        line_count_values = [int(item.get("line_count", 0) or 0) for item in phrase_items]
        mora_values = [float(item.get("average_mora_count", 0.0) or 0.0) for item in phrase_items]
        cadence_votes = [safe_text(item.get("cadence_shape")) for item in phrase_items + line_items]
        repetition_counts = [int(item.get("repetition_count", 0) or 0) for item in phrase_items]
        hook_density_values = [
            int(item.get("hook_line_count", 0) or 0) for item in chorus_items
        ] or [
            int(item.get("hook_hit_count", 0) or 0) for item in phrase_items
        ]
        title_return_values = [
            int(item.get("title_return_count", 0) or 0) for item in chorus_items
        ]
        lexical_family_votes = [
            safe_text(item.get("dominant_lexical_family"))
            for item in phrase_items + chorus_items
            if safe_text(item.get("dominant_lexical_family"))
        ] + [
            safe_text(item.get("lexical_family"))
            for item in line_items
            if safe_text(item.get("lexical_family"))
        ]
        repetition_payoff_votes = [
            safe_text(item.get("repetition_payoff"))
            for item in chorus_items
            if safe_text(item.get("repetition_payoff"))
        ]

        cadence_family = _top(cadence_votes, 1)[0] if cadence_votes else ""
        hook_density_band = _int_band(hook_density_values, floor_value=0)
        title_return_band = _int_band(title_return_values, floor_value=0)
        line_target_range = _int_band(line_count_values, floor_value=1)
        mora_band = _float_band(mora_values, floor_value=0.0)
        lexical_family_bias = _top(lexical_family_votes, 3)

        section_priors[section_name] = {
            "line_target_range": [line_target_range["min"], line_target_range["max"]],
            "mora_band": [int(round(mora_band["min"])), int(round(mora_band["max"]))],
            "cadence_family": cadence_family,
            "preferred_line_target": line_target_range["median"],
            "preferred_mora_target": int(round(mora_band["median"])),
            "repetition_budget": _repetition_budget(
                section_name,
                repetition_counts,
                repetition_payoff_votes,
                hook_density_band,
            ),
            "title_return_band": [title_return_band["min"], title_return_band["max"]],
            "preferred_title_return_count": title_return_band["median"],
            "hook_density_band": _hook_density_label(hook_density_band),
            "section_contrast_role": _section_contrast_role(section_name),
            "closure_strength_target": _closure_strength_target(section_name, cadence_family),
            "lexical_family_bias": lexical_family_bias,
            "sample_count": len(phrase_items) + len(chorus_items),
        }

    shared_chorus_prior = section_priors.get("chorus", {})
    shared_chorus_target = list(shared_chorus_prior.get("line_target_range", []))
    chorus_mid = int(shared_chorus_prior.get("preferred_line_target", 0) or 0)
    if chorus_mid:
        shared_chorus_target = [max(4, chorus_mid - 1), max(chorus_mid, 4)]
    return {
        "available": bool(section_priors),
        "mode_id": safe_text(mode_id),
        "artists": selected_artists,
        "record_counts": {
            "line": len(line_records),
            "phrase": len(phrase_records),
            "chorus": len(chorus_records),
        },
        "shared": {
            "chorus_line_target": shared_chorus_target,
            "hook_density_band": safe_text(shared_chorus_prior.get("hook_density_band"), "medium"),
            "repetition_pressure": "high" if int(shared_chorus_prior.get("repetition_budget", 0) or 0) >= 2 else "medium",
        },
        "sections": section_priors,
    }


def load_lyric_behavior_priors(
    project_root: Path,
    *,
    artist_ids: list[str] | None = None,
    mode_id: str = "",
    behavior_root: Path | None = None,
) -> dict[str, Any]:
    if behavior_root:
        behavior_roots = [behavior_root.resolve()]
    else:
        behavior_roots = []
        for content_root in candidate_content_roots(project_root):
            candidate_root = (content_root / "datasets" / "training" / "lyric_behavior").resolve()
            if candidate_root not in behavior_roots:
                behavior_roots.append(candidate_root)
    selected_artists = unique_preserve_order(
        [safe_text(artist) for artist in (artist_ids or DEFAULT_CALIBRATION_ARTISTS) if safe_text(artist)]
    )

    manifests: list[Path] = []
    for root in behavior_roots:
        if not root.exists():
            continue
        for manifest_path in sorted(root.rglob("lyric_behavior_manifest.json")):
            if manifest_path not in manifests:
                manifests.append(manifest_path)
    loaded_manifest_paths: list[str] = []
    loaded_outputs: list[str] = []
    line_records: list[dict[str, Any]] = []
    phrase_records: list[dict[str, Any]] = []
    chorus_records: list[dict[str, Any]] = []

    for manifest_path in manifests:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        manifest_artists = [safe_text(artist) for artist in manifest.get("artists", []) if safe_text(artist)]
        if selected_artists and manifest_artists and not any(artist in selected_artists for artist in manifest_artists):
            continue
        outputs = manifest.get("outputs", {}) if isinstance(manifest.get("outputs", {}), dict) else {}
        line_path = Path(safe_text(outputs.get("line_behavior_records")))
        phrase_path = Path(safe_text(outputs.get("phrase_behavior_records")))
        chorus_path = Path(safe_text(outputs.get("chorus_behavior_records")))
        if not line_path.exists() or not phrase_path.exists() or not chorus_path.exists():
            continue

        loaded_manifest_paths.append(str(manifest_path))
        loaded_outputs.extend([str(line_path), str(phrase_path), str(chorus_path)])
        line_records.extend(_load_jsonl(line_path))
        phrase_records.extend(_load_jsonl(phrase_path))
        chorus_records.extend(_load_jsonl(chorus_path))

    priors = summarize_behavior_priors(
        line_records=line_records,
        phrase_records=phrase_records,
        chorus_records=chorus_records,
        mode_id=mode_id,
        artist_ids=selected_artists,
    )
    return {
        **priors,
        "behavior_root": str(behavior_roots[0]) if behavior_roots else "",
        "behavior_roots": [str(root) for root in behavior_roots],
        "loaded_manifest_paths": loaded_manifest_paths,
        "loaded_outputs": unique_preserve_order(loaded_outputs),
    }


def build_behavior_priors(
    project_root: Path,
    *,
    artist_ids: list[str] | None = None,
    mode_id: str = "",
    behavior_root: Path | None = None,
) -> dict[str, Any]:
    calibration_artist_ids = unique_preserve_order(
        list(DEFAULT_CALIBRATION_ARTISTS)
        + [safe_text(artist) for artist in (artist_ids or []) if safe_text(artist)]
    )
    return load_lyric_behavior_priors(
        project_root,
        artist_ids=calibration_artist_ids,
        mode_id=mode_id,
        behavior_root=behavior_root,
    )
