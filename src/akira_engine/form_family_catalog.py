from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

from .lyric_behavior_priors import DEFAULT_CALIBRATION_ARTISTS
from .lyric_utils import safe_text, unique_preserve_order
from .songwriter_io import candidate_content_roots


_FAMILY_METADATA = {
    "compressed_hook": {
        "display_name": "Compressed Hook",
        "description": "Short, chant-like choruses with strong hook return pressure and compact mora density.",
    },
    "expansive_statement": {
        "display_name": "Expansive Statement",
        "description": "Longer chorus lines with lower hook repetition pressure and more declarative phrasing.",
    },
    "hybrid_release": {
        "display_name": "Hybrid Release",
        "description": "Mixed chorus strategy combining moderate hook return with mid-length statement lines.",
    },
}


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


def _int_band(values: list[int], *, fallback: int = 0) -> list[int]:
    clean = sorted(int(value) for value in values)
    if not clean:
        return [fallback, fallback]
    mid = int(round(median(clean)))
    low = max(min(clean), mid - 1)
    high = min(max(clean), mid + 1)
    return [int(low), int(max(low, high))]


def _float_band(values: list[float], *, fallback: float = 0.0) -> list[float]:
    clean = sorted(float(value) for value in values)
    if not clean:
        return [fallback, fallback]
    mid = float(median(clean))
    low = max(min(clean), mid - 2.0)
    high = min(max(clean), mid + 2.0)
    return [round(low, 2), round(max(low, high), 2)]


def _dominant(values: list[str], default: str = "") -> str:
    counts = Counter(value for value in values if safe_text(value))
    if not counts:
        return default
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _sorted_counter_keys(counter: Counter[str], *, limit: int = 6) -> list[str]:
    return [value for value, _ in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def _discover_behavior_manifests(project_root: Path, behavior_root: Path | None) -> list[Path]:
    if behavior_root is not None:
        roots = [behavior_root.resolve()]
    else:
        roots: list[Path] = []
        for content_root in candidate_content_roots(project_root):
            candidate = (content_root / "datasets" / "training" / "lyric_behavior").resolve()
            if candidate not in roots:
                roots.append(candidate)
    manifests: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for manifest_path in sorted(root.rglob("lyric_behavior_manifest.json")):
            if manifest_path not in manifests:
                manifests.append(manifest_path)
    return manifests


def _load_behavior_records(
    project_root: Path,
    *,
    artists: list[str] | None = None,
    behavior_root: Path | None = None,
) -> dict[str, Any]:
    selected_artists = unique_preserve_order(
        [safe_text(artist) for artist in (artists or DEFAULT_CALIBRATION_ARTISTS) if safe_text(artist)]
    )
    manifests = _discover_behavior_manifests(project_root, behavior_root)
    loaded_manifest_paths: list[str] = []
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
        outputs = manifest.get("outputs", {}) if isinstance(manifest.get("outputs"), dict) else {}
        line_path = Path(safe_text(outputs.get("line_behavior_records")))
        phrase_path = Path(safe_text(outputs.get("phrase_behavior_records")))
        chorus_path = Path(safe_text(outputs.get("chorus_behavior_records")))
        if not line_path.exists() or not phrase_path.exists() or not chorus_path.exists():
            continue
        loaded_manifest_paths.append(str(manifest_path))
        line_records.extend(_load_jsonl(line_path))
        phrase_records.extend(_load_jsonl(phrase_path))
        chorus_records.extend(_load_jsonl(chorus_path))

    if selected_artists:
        selected = set(selected_artists)
        line_records = [record for record in line_records if safe_text(record.get("artist_id")) in selected]
        phrase_records = [record for record in phrase_records if safe_text(record.get("artist_id")) in selected]
        chorus_records = [record for record in chorus_records if safe_text(record.get("artist_id")) in selected]

    return {
        "artists": selected_artists,
        "line_records": line_records,
        "phrase_records": phrase_records,
        "chorus_records": chorus_records,
        "loaded_manifest_paths": loaded_manifest_paths,
    }


def _classify_form_family(track_summary: dict[str, Any]) -> tuple[str, str]:
    hook_avg = float(track_summary.get("chorus_hook_avg", 0.0) or 0.0)
    title_avg = float(track_summary.get("title_return_avg", 0.0) or 0.0)
    mora_avg = float(track_summary.get("chorus_mora_avg", 0.0) or 0.0)
    payoff = safe_text(track_summary.get("payoff_mode"))

    if hook_avg >= 2.0 and (title_avg >= 1.0 or mora_avg <= 11.0):
        return "compressed_hook", "high hook density with compact or title-return chorus behavior"
    if mora_avg >= 15.0 and hook_avg <= 1.0:
        return "expansive_statement", "long chorus lines with lower hook-return pressure"
    if payoff == "high" and hook_avg >= 1.5:
        return "compressed_hook", "high-payoff chorus repeats dominate the release shape"
    return "hybrid_release", "mixed chorus behavior without single dominant hook or long-form statement bias"


def _summarize_track_forms(
    *,
    line_records: list[dict[str, Any]],
    phrase_records: list[dict[str, Any]],
    chorus_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    track_rows: dict[str, dict[str, Any]] = {}

    def ensure_track(track_id: str, artist_id: str) -> dict[str, Any]:
        row = track_rows.setdefault(
            track_id,
            {
                "track_id": track_id,
                "artist_id": artist_id,
                "sections": [],
                "section_count": 0,
                "chorus_hook_values": [],
                "chorus_title_values": [],
                "chorus_mora_values": [],
                "payoff_votes": [],
                "lexical_family_votes": [],
                "cadence_votes": [],
            },
        )
        if artist_id and not row["artist_id"]:
            row["artist_id"] = artist_id
        return row

    for record in phrase_records:
        track_id = safe_text(record.get("track_id"))
        if not track_id:
            continue
        row = ensure_track(track_id, safe_text(record.get("artist_id")))
        section_name = safe_text(record.get("section_name"))
        if section_name and section_name not in row["sections"]:
            row["sections"].append(section_name)
        cadence = safe_text(record.get("cadence_shape"))
        if cadence:
            row["cadence_votes"].append(cadence)
        family = safe_text(record.get("dominant_lexical_family"))
        if family:
            row["lexical_family_votes"].append(family)

    for record in line_records:
        track_id = safe_text(record.get("track_id"))
        if not track_id:
            continue
        row = ensure_track(track_id, safe_text(record.get("artist_id")))
        cadence = safe_text(record.get("cadence_shape"))
        if cadence:
            row["cadence_votes"].append(cadence)
        family = safe_text(record.get("lexical_family"))
        if family:
            row["lexical_family_votes"].append(family)

    for record in chorus_records:
        track_id = safe_text(record.get("track_id"))
        if not track_id:
            continue
        row = ensure_track(track_id, safe_text(record.get("artist_id")))
        row["chorus_hook_values"].append(int(record.get("hook_line_count", 0) or 0))
        row["chorus_title_values"].append(int(record.get("title_return_count", 0) or 0))
        row["chorus_mora_values"].append(float(record.get("average_mora_count", 0.0) or 0.0))
        payoff = safe_text(record.get("repetition_payoff"))
        if payoff:
            row["payoff_votes"].append(payoff)
        family = safe_text(record.get("dominant_lexical_family"))
        if family:
            row["lexical_family_votes"].append(family)

    summaries: list[dict[str, Any]] = []
    for row in track_rows.values():
        if not row["chorus_mora_values"]:
            continue
        chorus_hook_avg = round(sum(row["chorus_hook_values"]) / len(row["chorus_hook_values"]), 2)
        chorus_title_avg = round(sum(row["chorus_title_values"]) / len(row["chorus_title_values"]), 2)
        chorus_mora_avg = round(sum(row["chorus_mora_values"]) / len(row["chorus_mora_values"]), 2)
        dominant_lexical_families = _sorted_counter_keys(Counter(row["lexical_family_votes"]), limit=4)
        dominant_cadences = _sorted_counter_keys(Counter(row["cadence_votes"]), limit=6)
        summary = {
            "track_id": row["track_id"],
            "artist_id": row["artist_id"],
            "sections": row["sections"],
            "section_count": len(row["sections"]),
            "chorus_hook_avg": chorus_hook_avg,
            "title_return_avg": chorus_title_avg,
            "chorus_mora_avg": chorus_mora_avg,
            "payoff_mode": _dominant(row["payoff_votes"], "medium"),
            "dominant_lexical_families": dominant_lexical_families,
            "dominant_cadences": dominant_cadences,
        }
        family_id, reason = _classify_form_family(summary)
        summary["form_family_id"] = family_id
        summary["family_reason"] = reason
        summaries.append(summary)

    return sorted(summaries, key=lambda item: (item["artist_id"], item["track_id"]))


def _build_family_priors(track_summaries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for summary in track_summaries:
        grouped[safe_text(summary.get("form_family_id"))].append(summary)

    family_priors: dict[str, dict[str, Any]] = {}
    for family_id, rows in grouped.items():
        if not family_id:
            continue
        artist_counts = Counter(safe_text(row.get("artist_id")) for row in rows if safe_text(row.get("artist_id")))
        cadence_counts = Counter(
            cadence
            for row in rows
            for cadence in row.get("dominant_cadences", [])
            if safe_text(cadence)
        )
        section_counts = [int(row.get("section_count", 0) or 0) for row in rows]
        hook_values = [float(row.get("chorus_hook_avg", 0.0) or 0.0) for row in rows]
        title_values = [float(row.get("title_return_avg", 0.0) or 0.0) for row in rows]
        mora_values = [float(row.get("chorus_mora_avg", 0.0) or 0.0) for row in rows]
        family_counts = Counter(
            family
            for row in rows
            for family in row.get("dominant_lexical_families", [])
            if safe_text(family)
        )
        examples = sorted(
            rows,
            key=lambda row: (
                -float(row.get("chorus_hook_avg", 0.0) or 0.0),
                float(row.get("chorus_mora_avg", 0.0) or 0.0),
                safe_text(row.get("track_id")),
            ),
        )[:5]
        family_priors[family_id] = {
            "family_id": family_id,
            "display_name": _FAMILY_METADATA[family_id]["display_name"],
            "description": _FAMILY_METADATA[family_id]["description"],
            "track_count": len(rows),
            "artist_distribution": dict(sorted(artist_counts.items())),
            "section_count_band": _int_band(section_counts, fallback=0),
            "chorus_hook_band": _float_band(hook_values, fallback=0.0),
            "title_return_band": _float_band(title_values, fallback=0.0),
            "chorus_mora_band": _float_band(mora_values, fallback=0.0),
            "dominant_payoff_modes": _sorted_counter_keys(
                Counter(safe_text(row.get("payoff_mode")) for row in rows if safe_text(row.get("payoff_mode"))),
                limit=3,
            ),
            "dominant_cadences": _sorted_counter_keys(cadence_counts, limit=6),
            "dominant_lexical_families": _sorted_counter_keys(family_counts, limit=4),
            "example_tracks": [safe_text(row.get("track_id")) for row in examples],
        }
    return family_priors


def build_form_family_catalog(
    project_root: Path,
    *,
    artists: list[str] | None = None,
    behavior_root: Path | None = None,
    output_root: Path | None = None,
    catalog_name: str = "calibration_v1",
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_output_root = (output_root or (final_project_root / "datasets" / "training" / "form_families")).resolve()
    final_catalog_root = (final_output_root / catalog_name).resolve()
    final_catalog_root.mkdir(parents=True, exist_ok=True)

    loaded = _load_behavior_records(
        final_project_root,
        artists=artists,
        behavior_root=behavior_root,
    )
    track_summaries = _summarize_track_forms(
        line_records=loaded["line_records"],
        phrase_records=loaded["phrase_records"],
        chorus_records=loaded["chorus_records"],
    )
    family_priors = _build_family_priors(track_summaries)

    track_assignments_path = final_catalog_root / "track_form_assignments.jsonl"
    track_assignments_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in track_summaries),
        encoding="utf-8",
    )

    catalog_path = final_catalog_root / "form_family_catalog.json"
    catalog_payload = {
        "schema_version": "1.0",
        "catalog_name": catalog_name,
        "project_root": str(final_project_root),
        "artists": loaded["artists"],
        "track_count": len(track_summaries),
        "families": family_priors,
    }
    catalog_path.write_text(json.dumps(catalog_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    family_counts = Counter(row["form_family_id"] for row in track_summaries)
    manifest = {
        "schema_version": "1.0",
        "record_type": "form_family_catalog_manifest",
        "catalog_name": catalog_name,
        "project_root": str(final_project_root),
        "artists": loaded["artists"],
        "counts": {
            "track_assignments": len(track_summaries),
            "families": len(family_priors),
            "compressed_hook": int(family_counts.get("compressed_hook", 0)),
            "expansive_statement": int(family_counts.get("expansive_statement", 0)),
            "hybrid_release": int(family_counts.get("hybrid_release", 0)),
        },
        "loaded_manifest_paths": loaded["loaded_manifest_paths"],
        "outputs": {
            "track_assignments": str(track_assignments_path),
            "form_family_catalog": str(catalog_path),
        },
    }
    manifest_path = final_catalog_root / "form_family_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest
