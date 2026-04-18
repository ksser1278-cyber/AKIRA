from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .conditioning_brief_dataset import canonical_section
from .japanese_lyric_features import mora_unit_estimate, normalize_title_variants
from .lexical_family_bank import classify_term_family, is_cliche_term
from .lyric_utils import safe_text
from .songwriter_io import load_conditioning_records, load_generated_mode_assignments


_VOWEL_TABLE = {
    "あ": "a", "か": "a", "さ": "a", "た": "a", "な": "a", "は": "a", "ま": "a", "や": "a", "ら": "a", "わ": "a", "が": "a", "ざ": "a", "だ": "a", "ば": "a", "ぱ": "a",
    "い": "i", "き": "i", "し": "i", "ち": "i", "に": "i", "ひ": "i", "み": "i", "り": "i", "ぎ": "i", "じ": "i", "ぢ": "i", "び": "i", "ぴ": "i",
    "う": "u", "く": "u", "す": "u", "つ": "u", "ぬ": "u", "ふ": "u", "む": "u", "ゆ": "u", "る": "u", "ぐ": "u", "ず": "u", "づ": "u", "ぶ": "u", "ぷ": "u",
    "え": "e", "け": "e", "せ": "e", "て": "e", "ね": "e", "へ": "e", "め": "e", "れ": "e", "げ": "e", "ぜ": "e", "で": "e", "べ": "e", "ぺ": "e",
    "お": "o", "こ": "o", "そ": "o", "と": "o", "の": "o", "ほ": "o", "も": "o", "よ": "o", "ろ": "o", "を": "o", "ご": "o", "ぞ": "o", "ど": "o", "ぼ": "o", "ぽ": "o",
}
_KATAKANA_TO_HIRAGANA_OFFSET = ord("ァ") - ord("ぁ")


def _to_hiragana(text: str) -> str:
    out: list[str] = []
    for ch in text:
        if "ァ" <= ch <= "ヶ":
            out.append(chr(ord(ch) - _KATAKANA_TO_HIRAGANA_OFFSET))
        else:
            out.append(ch)
    return "".join(out)


def _vowel_profile(text: str) -> dict[str, int]:
    counts = {"a": 0, "i": 0, "u": 0, "e": 0, "o": 0}
    hira = _to_hiragana(text)
    for ch in hira:
        vowel = _VOWEL_TABLE.get(ch)
        if vowel:
            counts[vowel] += 1
    return counts


def _dominant_lexical_family(text: str) -> str:
    tokens = re.findall(r"[\u3041-\u3096\u30a1-\u30fa\u30fc\u4e00-\u9fff]{1,8}", text)
    families = [classify_term_family(token) for token in tokens]
    families = [family for family in families if family]
    if not families:
        return ""
    return Counter(families).most_common(1)[0][0]


def _tension_state(section_name: str) -> str:
    mapping = {
        "intro": "setup",
        "verse_1": "pressure",
        "verse_2": "pressure",
        "pre_chorus": "pressure",
        "pre_chorus_2": "pressure",
        "chorus": "release",
        "bridge": "break",
        "chorus_final": "release",
        "outro": "aftermath",
    }
    return mapping.get(section_name, "pressure")


def _cadence_shape(line: str, section_name: str) -> str:
    mora = mora_unit_estimate(line)
    if section_name == "chorus_final":
        return "explosive"
    if section_name.startswith("chorus"):
        return "compressed" if mora <= 14 else "held"
    if section_name.startswith("pre_chorus"):
        return "rising"
    if section_name == "bridge":
        return "suspended"
    return "balanced" if mora <= 18 else "extended"


def _repetition_role(line: str, *, hook_lines: set[str], seen: Counter[str], section_name: str) -> str:
    if line in hook_lines:
        return "hook_return"
    if seen[line] > 1 and section_name.startswith("chorus"):
        return "tighten"
    if seen[line] > 1:
        return "echo"
    if section_name == "chorus_final":
        return "release"
    return "new"


def _title_offset(line: str, title_variants: list[str]) -> int | None:
    compact = re.sub(r"\s+", "", line)
    for variant in title_variants:
        marker = re.sub(r"\s+", "", variant)
        idx = compact.find(marker)
        if idx >= 0:
            return idx
    return None


def _hook_distance(section_index: int, chorus_indices: list[int]) -> int | None:
    if not chorus_indices:
        return None
    return min(abs(section_index - idx) for idx in chorus_indices)


def _iter_artist_ids(project_root: Path, artists: list[str] | None) -> list[str]:
    if artists:
        return [safe_text(artist) for artist in artists if safe_text(artist)]
    artist_root = project_root / "artists"
    if not artist_root.exists():
        return []
    return sorted(path.name for path in artist_root.iterdir() if path.is_dir())


def build_lyric_behavior_dataset(
    *,
    project_root: Path,
    artists: list[str] | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_output_root = (output_root or (final_project_root / "datasets" / "training" / "lyric_behavior")).resolve()
    final_output_root.mkdir(parents=True, exist_ok=True)

    line_path = final_output_root / "line_behavior_records.jsonl"
    phrase_path = final_output_root / "phrase_behavior_records.jsonl"
    chorus_path = final_output_root / "chorus_behavior_records.jsonl"

    line_records: list[dict[str, Any]] = []
    phrase_records: list[dict[str, Any]] = []
    chorus_records: list[dict[str, Any]] = []
    artist_ids = _iter_artist_ids(final_project_root, artists)

    for artist_id in artist_ids:
        assignments = load_generated_mode_assignments(artist_id)
        for record in load_conditioning_records(artist_id):
            identity = record.get("track_identity", {}) if isinstance(record.get("track_identity", {}), dict) else {}
            lyric_ground_truth = record.get("lyric_ground_truth", {}) if isinstance(record.get("lyric_ground_truth", {}), dict) else {}
            track_id = safe_text(identity.get("track_id"))
            if not track_id:
                continue
            sections = lyric_ground_truth.get("sections", [])
            if not isinstance(sections, list) or not sections:
                continue

            title = safe_text(identity.get("title"))
            title_core = safe_text(identity.get("title_core"))
            title_variants = normalize_title_variants(title, title_core)
            mode_id = safe_text(record.get("primary_mode") or record.get("mode_id") or assignments.get(track_id))
            hook_lines = {
                safe_text(line)
                for line in lyric_ground_truth.get("hook_lines", [])
                if safe_text(line)
            }
            index_map: dict[str, int] = {}
            canonical_sections: list[str] = []
            for section in sections:
                canonical_sections.append(
                    canonical_section(
                        safe_text(section.get("section_type")),
                        safe_text(section.get("jp_section_role")),
                        index_map,
                    )
                )
            chorus_indices = [idx for idx, name in enumerate(canonical_sections) if name.startswith("chorus")]
            seen_lines = Counter(
                safe_text(line)
                for section in sections
                for line in section.get("lines", [])
                if safe_text(line)
            )

            for section_index, section in enumerate(sections):
                section_name = canonical_sections[section_index]
                lines = [safe_text(line) for line in section.get("lines", []) if safe_text(line)]
                if not lines:
                    continue
                section_hook_hits = sum(1 for line in lines if line in hook_lines)
                section_record_id = f"{track_id}:{section_name}:{section_index}"
                phrase_records.append(
                    {
                        "schema_version": "1.0",
                        "record_type": "phrase_behavior_record",
                        "record_id": section_record_id,
                        "track_id": track_id,
                        "artist_id": artist_id,
                        "mode_id": mode_id,
                        "section_name": section_name,
                        "section_index": section_index,
                        "line_count": len(lines),
                        "average_mora_count": round(sum(mora_unit_estimate(line) for line in lines) / len(lines), 2),
                        "cadence_shape": _cadence_shape(lines[-1], section_name),
                        "tension_state": _tension_state(section_name),
                        "repetition_count": len(lines) - len(set(lines)),
                        "hook_hit_count": section_hook_hits,
                        "dominant_lexical_family": _dominant_lexical_family(" ".join(lines)),
                    }
                )
                if section_name.startswith("chorus"):
                    chorus_records.append(
                        {
                            "schema_version": "1.0",
                            "record_type": "chorus_behavior_record",
                            "record_id": section_record_id,
                            "track_id": track_id,
                            "artist_id": artist_id,
                            "mode_id": mode_id,
                            "section_name": section_name,
                            "section_index": section_index,
                            "hook_line_count": section_hook_hits,
                            "title_return_count": sum(1 for line in lines if _title_offset(line, title_variants) is not None),
                            "average_line_length": round(sum(len(line.replace(" ", "")) for line in lines) / len(lines), 2),
                            "average_mora_count": round(sum(mora_unit_estimate(line) for line in lines) / len(lines), 2),
                            "repetition_payoff": "high" if section_hook_hits >= 2 or len(set(lines)) < len(lines) else "medium",
                            "dominant_lexical_family": _dominant_lexical_family(" ".join(lines)),
                        }
                    )

                for line_index, line in enumerate(lines):
                    line_records.append(
                        {
                            "schema_version": "1.0",
                            "record_type": "line_behavior_record",
                            "record_id": f"{section_record_id}:{line_index}",
                            "track_id": track_id,
                            "artist_id": artist_id,
                            "mode_id": mode_id,
                            "section_name": section_name,
                            "section_index": section_index,
                            "line_index": line_index,
                            "surface_text": line,
                            "line_length": len(line.replace(" ", "")),
                            "mora_count": mora_unit_estimate(line),
                            "vowel_profile": _vowel_profile(line),
                            "repetition_role": _repetition_role(line, hook_lines=hook_lines, seen=seen_lines, section_name=section_name),
                            "tension_state": _tension_state(section_name),
                            "cadence_shape": _cadence_shape(line, section_name),
                            "hook_distance": _hook_distance(section_index, chorus_indices),
                            "title_return_offset": _title_offset(line, title_variants),
                            "lexical_family": _dominant_lexical_family(line),
                            "cliche_risk": "high" if is_cliche_term(line) else "low",
                        }
                    )

    line_path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in line_records), encoding="utf-8")
    phrase_path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in phrase_records), encoding="utf-8")
    chorus_path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in chorus_records), encoding="utf-8")

    manifest = {
        "schema_version": "1.0",
        "record_type": "lyric_behavior_manifest",
        "project_root": str(final_project_root),
        "output_root": str(final_output_root),
        "artists": artist_ids,
        "counts": {
            "artists": len(artist_ids),
            "line_behavior_records": len(line_records),
            "phrase_behavior_records": len(phrase_records),
            "chorus_behavior_records": len(chorus_records),
        },
        "outputs": {
            "line_behavior_records": str(line_path),
            "phrase_behavior_records": str(phrase_path),
            "chorus_behavior_records": str(chorus_path),
        },
    }
    manifest_path = final_output_root / "lyric_behavior_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest
