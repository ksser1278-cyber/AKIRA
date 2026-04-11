from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CONDITIONING_CACHE: dict[str, list[dict[str, Any]]] = {}
GENERATED_MODE_ASSIGNMENT_CACHE: dict[str, dict[str, str]] = {}

LOW_SIGNAL_CONDITIONING_ATOMS = {
    "意味", "容易く", "正確", "感情", "判断", "分別", "証明", "不明瞭", "証明しよう",
    "どうし", "見抜いて", "吐いて", "打つんだ", "聞き", "逸ら", "分けてみせ", "論理",
    "不合理な", "禁じ",
}

GENERIC_HOOK_ATOMS = {"心", "声", "夜", "夢", "光", "君", "僕", "私", "明日", "未来", "名前"}

CONDITIONED_DECISION_BANK = [
    "それでも黙らない",
    "壊れたまま飲み込まない",
    "ここから誤魔化さない",
    "ここから飲み込まない",
    "喉の奥で噛み砕く",
    "このまま引き受ける",
]

CONDITIONED_RELEASE_BANK = [
    "綺麗に切れなくても",
    "答えにならなくても",
    "誤差のままでも",
    "うまく名前がなくても",
]



def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def candidate_content_roots(root: Path | None = None) -> list[Path]:
    base_root = root or project_root()
    roots: list[Path] = [base_root]
    quarantine_root = base_root / "_quarantine"
    if quarantine_root.exists():
        archives = sorted(
            (path / "archive" for path in quarantine_root.iterdir() if (path / "archive").is_dir()),
            key=lambda path: path.parent.name,
            reverse=True,
        )
        for archive_root in archives:
            if archive_root not in roots:
                roots.append(archive_root)
    return roots


def _first_existing_relative_path(relative_path: Path, *, root: Path | None = None) -> Path | None:
    for content_root in candidate_content_roots(root):
        candidate = content_root / relative_path
        if candidate.exists():
            return candidate
    return None


def conditioning_reference_dirs(artist_id: str, *, root: Path | None = None) -> list[Path]:
    clean_artist_id = str(artist_id).strip()
    if not clean_artist_id:
        return []
    reference_dirs: list[Path] = []
    relative_dirs = (
        Path("data") / clean_artist_id / "reference_tracks",
        Path("data") / "reference_tracks" / clean_artist_id,
    )
    for content_root in candidate_content_roots(root):
        for relative_dir in relative_dirs:
            candidate = content_root / relative_dir
            if candidate.exists() and candidate not in reference_dirs:
                reference_dirs.append(candidate)
    return reference_dirs


def load_artist_profile(artist_id: str) -> dict[str, Any] | None:
    clean_artist_id = str(artist_id).strip()
    if not clean_artist_id:
        return None

    profile_path = _first_existing_relative_path(Path("artists") / clean_artist_id / "profile.json")
    if not profile_path or not profile_path.exists():
        return None

    try:
        return json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_structure_profile(artist_id: str) -> dict[str, Any] | None:
    clean_artist_id = str(artist_id).strip()
    if not clean_artist_id:
        return None

    profile_path = _first_existing_relative_path(Path("artists") / clean_artist_id / "structure_profile.json")
    if not profile_path or not profile_path.exists():
        return None

    try:
        return json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_representative_demo_profile(artist_id: str) -> dict[str, Any] | None:
    clean_artist_id = str(artist_id).strip()
    if not clean_artist_id:
        return None

    profile_path = _first_existing_relative_path(
        Path("artists") / clean_artist_id / "representative_demo_profile.json"
    )
    if not profile_path or not profile_path.exists():
        return None

    try:
        return json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def normalize_lookup_text(value: Any) -> str:
    raw = str(value or "").strip().lower()
    return re.sub(r"[^0-9a-z\u3041-\u3096\u30a1-\u30fa\u30fc\u4e00-\u9fff]+", "", raw)


def load_conditioning_records(artist_id: str) -> list[dict[str, Any]]:
    clean_artist_id = str(artist_id).strip()
    if not clean_artist_id:
        return []
    if clean_artist_id in CONDITIONING_CACHE:
        return CONDITIONING_CACHE[clean_artist_id]

    records: list[dict[str, Any]] = []
    seen_paths: set[Path] = set()
    for reference_dir in conditioning_reference_dirs(clean_artist_id):
        if not reference_dir.exists():
            continue
        for path in sorted(reference_dir.glob("*.conditioning.json")):
            if path in seen_paths:
                continue
            seen_paths.add(path)
            try:
                records.append(json.loads(path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
    CONDITIONING_CACHE[clean_artist_id] = records
    return records


def load_generated_mode_assignments(artist_id: str) -> dict[str, str]:
    clean_artist_id = str(artist_id).strip()
    if not clean_artist_id:
        return {}
    if clean_artist_id in GENERATED_MODE_ASSIGNMENT_CACHE:
        return GENERATED_MODE_ASSIGNMENT_CACHE[clean_artist_id]

    profile_path = _first_existing_relative_path(
        Path("artists") / clean_artist_id / "style_prompt_profile.generated.json"
    )
    assignments: dict[str, str] = {}
    if profile_path and profile_path.exists():
        try:
            payload = json.loads(profile_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        generated = payload.get("generated_from_conditioning", {})
        for item in generated.get("track_mode_assignments", []):
            mode_id = str(item.get("mode_id", "")).strip()
            if not mode_id:
                continue
            for key in [
                item.get("track_id"),
                item.get("title_core"),
                item.get("title"),
            ]:
                normalized = normalize_lookup_text(key)
                if normalized:
                    assignments[normalized] = mode_id
    GENERATED_MODE_ASSIGNMENT_CACHE[clean_artist_id] = assignments
    return assignments


def matching_conditioning_record(record: dict[str, Any]) -> dict[str, Any] | None:
    artist_id = str(record.get("artist_id", "")).strip()
    if not artist_id:
        return None

    track_id = str(record.get("track_id", "")).strip()
    title = str(record.get("title", "")).split("(")[0].strip()
    lookup_keys = {normalize_lookup_text(track_id), normalize_lookup_text(title)}
    lookup_keys.discard("")

    for conditioning in load_conditioning_records(artist_id):
        identity = conditioning.get("track_identity", {})
        provenance = conditioning.get("source_provenance", {})
        candidate_keys = {
            normalize_lookup_text(identity.get("track_id")),
            normalize_lookup_text(identity.get("title")),
            normalize_lookup_text(identity.get("title_core")),
        }
        for source in provenance.get("lyric_sources", []):
            candidate_keys.add(normalize_lookup_text(source.get("label")))
        candidate_keys.discard("")
        if lookup_keys & candidate_keys:
            return conditioning
    return None


def resolve_primary_mode(record: dict[str, Any], conditioning: dict[str, Any] | None) -> tuple[str, str]:
    artist_id = str(record.get("artist_id", "")).strip()
    generated_assignments = load_generated_mode_assignments(artist_id)
    if conditioning and generated_assignments:
        identity = conditioning.get("track_identity", {})
        provenance = conditioning.get("source_provenance", {})
        lookup_keys = [
            identity.get("track_id"),
            identity.get("title"),
            identity.get("title_core"),
        ]
        lookup_keys.extend(source.get("label") for source in provenance.get("lyric_sources", []))
        for key in lookup_keys:
            normalized = normalize_lookup_text(key)
            if normalized and normalized in generated_assignments:
                return generated_assignments[normalized], "conditioning_generated_profile"

    record_mode = str(record.get("target", {}).get("primary_mode", "")).strip()
    if record_mode:
        return record_mode, "record_target"
    return "intimate_confessional", "fallback_default"


def resolve_default_track_id(records: list[dict[str, Any]]) -> str | None:
    if not records:
        return None

    artist_id = str(records[0].get("artist_id", "")).strip()
    if not artist_id or any(str(record.get("artist_id", "")).strip() != artist_id for record in records):
        return None

    representative_profile = load_representative_demo_profile(artist_id)
    if not representative_profile:
        return None

    default_track_id = str(representative_profile.get("default_demo_track_id", "")).strip()
    if not default_track_id:
        return None

    if any(str(record.get("track_id", "")).strip() == default_track_id for record in records):
        return default_track_id
    return None
