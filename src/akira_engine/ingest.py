from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_MANIFEST_KEYS = {
    "schema_version",
    "artist_id",
    "artist_name",
    "language",
    "source_type",
    "collection_method",
    "tracks",
}

REQUIRED_TRACK_KEYS = {
    "track_id",
    "title",
    "lyric_path",
}

RAW_LYRIC_EXTENSIONS = {".txt", ".md"}
RAW_LYRIC_IGNORED_PREFIXES = ("put_", "_")

SECTION_PATTERN = re.compile(
    r"^(?:\[(?P<bracket>[^\]]+)\]|\((?P<paren>[^)]+)\)|(?P<plain>(?:intro|verse|pre[- ]?chorus|chorus|bridge|outro|refrain)(?:\s+\d+)?))$",
    re.IGNORECASE,
)


@dataclass
class IngestSummary:
    output_dir: Path
    total_tracks: int
    total_sections: int


@dataclass
class ManifestBootstrapSummary:
    manifest_path: Path
    track_count: int
    raw_dir: Path


def build_manifest_payload(
    *,
    artist_id: str,
    artist_name: str,
    language: str,
    source_type: str,
    collection_method: str,
    tracks: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "artist_name": artist_name,
        "language": language,
        "source_type": source_type,
        "collection_method": collection_method,
        "tracks": tracks,
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_MANIFEST_KEYS - manifest.keys())
    if missing:
        raise ValueError(f"Manifest is missing required keys: {', '.join(missing)}")
    if not manifest["tracks"]:
        raise ValueError("Manifest has no tracks.")

    invalid_tracks: list[int] = []
    duplicate_track_ids: list[str] = []
    seen_track_ids: set[str] = set()
    for index, track in enumerate(manifest["tracks"], start=1):
        missing_track_keys = REQUIRED_TRACK_KEYS - track.keys()
        if missing_track_keys:
            invalid_tracks.append(index)
            continue
        track_id = track["track_id"]
        if track_id in seen_track_ids:
            duplicate_track_ids.append(track_id)
        seen_track_ids.add(track_id)
    if invalid_tracks:
        bad_rows = ", ".join(str(index) for index in invalid_tracks)
        raise ValueError(f"Manifest tracks missing required keys at positions: {bad_rows}")
    if duplicate_track_ids:
        duplicates = ", ".join(sorted(set(duplicate_track_ids)))
        raise ValueError(f"Manifest has duplicate track_id values: {duplicates}")
    return manifest


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "untitled"


def title_from_filename(path: Path) -> str:
    title = path.stem.replace("_", " ").replace("-", " ")
    title = re.sub(r"\s+", " ", title).strip()
    return title or path.stem


def discover_raw_lyric_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        raise SystemExit(f"Raw lyric directory does not exist: {raw_dir.resolve()}")
    if not raw_dir.is_dir():
        raise SystemExit(f"Raw lyric path is not a directory: {raw_dir.resolve()}")

    files = [
        path
        for path in sorted(raw_dir.iterdir())
        if path.is_file()
        and path.suffix.lower() in RAW_LYRIC_EXTENSIONS
        and not path.name.lower().startswith(RAW_LYRIC_IGNORED_PREFIXES)
    ]
    if not files:
        raise SystemExit(
            "No usable lyric text files were found.\n"
            f"Directory checked: {raw_dir.resolve()}\n"
            "Add .txt or .md lyric files and rerun the command."
        )
    return files


def build_track_id_from_path(path: Path, index: int, used_track_ids: set[str]) -> str:
    base_id = slugify(path.stem)
    if base_id == "untitled":
        base_id = f"track_{index:02d}"

    candidate = base_id
    suffix = 2
    while candidate in used_track_ids:
        candidate = f"{base_id}_{suffix:02d}"
        suffix += 1

    used_track_ids.add(candidate)
    return candidate


def relative_manifest_path(target_path: Path, manifest_dir: Path) -> str:
    relative_path = os.path.relpath(target_path.resolve(), start=manifest_dir.resolve())
    return Path(relative_path).as_posix()


def bootstrap_manifest(
    *,
    artist_id: str,
    artist_name: str,
    raw_dir: Path,
    manifest_path: Path,
    language: str = "ja",
    source_type: str = "manual_text",
    collection_method: str = "Manual import from user-provided lyric files for real artist analysis.",
) -> ManifestBootstrapSummary:
    raw_files = discover_raw_lyric_files(raw_dir)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    used_track_ids: set[str] = set()
    tracks: list[dict[str, Any]] = []
    for index, raw_file in enumerate(raw_files, start=1):
        track_id = build_track_id_from_path(raw_file, index, used_track_ids)
        tracks.append(
            {
                "track_id": track_id,
                "title": title_from_filename(raw_file),
                "lyric_path": relative_manifest_path(raw_file, manifest_path.parent),
                "notes": f"Auto-generated from raw lyric file: {raw_file.name}",
            }
        )

    manifest = build_manifest_payload(
        artist_id=artist_id,
        artist_name=artist_name,
        language=language,
        source_type=source_type,
        collection_method=collection_method,
        tracks=tracks,
    )
    write_manifest(manifest_path, manifest)
    return ManifestBootstrapSummary(
        manifest_path=manifest_path,
        track_count=len(tracks),
        raw_dir=raw_dir,
    )


def normalize_line(line: str) -> str:
    line = line.replace("\u3000", " ")
    line = line.replace("\t", " ")
    line = re.sub(r"[ ]{2,}", " ", line)
    return line.strip()


def normalize_section_label(label: str) -> str:
    normalized = label.lower().strip()
    normalized = normalized.replace("-", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    tokens = normalized.split()
    if not tokens:
        return "unlabeled"

    base = tokens[0]
    number = tokens[1] if len(tokens) > 1 and tokens[1].isdigit() else None
    aliases = {
        "intro": "intro",
        "verse": "verse",
        "pre": "pre_chorus",
        "chorus": "chorus",
        "bridge": "bridge",
        "outro": "outro",
        "refrain": "refrain",
    }
    if normalized.startswith("pre chorus"):
        base_label = "pre_chorus"
    else:
        base_label = aliases.get(base, slugify(normalized))
    return f"{base_label}_{number}" if number else base_label


def detect_section_label(line: str) -> str | None:
    match = SECTION_PATTERN.match(line)
    if not match:
        return None
    label = match.group("bracket") or match.group("paren") or match.group("plain")
    if not label:
        return None
    return normalize_section_label(label)


def build_sections(lines: list[str]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current_label: str | None = None
    current_lines: list[str] = []
    unlabeled_count = 0

    def flush_section() -> None:
        nonlocal current_label, current_lines, unlabeled_count
        if not current_lines:
            current_label = None
            return
        label = current_label
        if label is None:
            unlabeled_count += 1
            label = f"unlabeled_{unlabeled_count}"
        section_text = "\n".join(current_lines)
        sections.append(
            {
                "section_id": len(sections) + 1,
                "label": label,
                "line_count": len(current_lines),
                "lines": current_lines[:],
                "text": section_text,
            }
        )
        current_lines = []
        current_label = None

    for line in lines:
        section_label = detect_section_label(line)
        if section_label is not None:
            flush_section()
            current_label = section_label
            continue
        if not line:
            flush_section()
            continue
        current_lines.append(line)

    flush_section()
    return sections


def normalized_text_from_sections(sections: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for section in sections:
        label = section["label"]
        text = section["text"]
        blocks.append(f"[{label}]\n{text}")
    return "\n\n".join(blocks)


def build_stats(raw_text: str, sections: list[dict[str, Any]]) -> dict[str, Any]:
    raw_lines = raw_text.splitlines()
    normalized_nonempty_lines = [
        line
        for section in sections
        for line in section["lines"]
        if line
    ]
    unique_lines = {line.lower() for line in normalized_nonempty_lines}
    repeated_lines = len(normalized_nonempty_lines) - len(unique_lines)
    return {
        "raw_line_count": len(raw_lines),
        "nonempty_line_count": len(normalized_nonempty_lines),
        "section_count": len(sections),
        "repeated_line_count": repeated_lines,
        "unique_line_ratio": round(
            len(unique_lines) / len(normalized_nonempty_lines), 3
        )
        if normalized_nonempty_lines
        else 0.0,
    }


def build_normalized_document(
    manifest: dict[str, Any],
    track: dict[str, Any],
    manifest_path: Path,
) -> dict[str, Any]:
    lyric_path = (manifest_path.parent / track["lyric_path"]).resolve()
    raw_text = lyric_path.read_text(encoding="utf-8")
    normalized_lines = [normalize_line(line) for line in raw_text.splitlines()]
    sections = build_sections(normalized_lines)
    stats = build_stats(raw_text, sections)

    return {
        "schema_version": "1.0",
        "artist_id": manifest["artist_id"],
        "artist_name": manifest["artist_name"],
        "track_id": track["track_id"],
        "title": track["title"],
        "language": manifest["language"],
        "source_type": manifest["source_type"],
        "collection_method": manifest["collection_method"],
        "source_manifest": str(manifest_path),
        "source_lyric_path": str(lyric_path),
        "source_url": track.get("source_url", ""),
        "source_site": track.get("source_site", ""),
        "notes": track.get("notes", ""),
        "raw_text": raw_text,
        "normalized_text": normalized_text_from_sections(sections),
        "sections": sections,
        "stats": stats,
    }


def default_output_dir() -> Path:
    return Path("lyrics") / "normalized"


def write_document(output_dir: Path, document: dict[str, Any]) -> Path:
    artist_dir = output_dir / document["artist_id"]
    artist_dir.mkdir(parents=True, exist_ok=True)
    output_path = artist_dir / f"{document['track_id']}.json"
    output_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path


def normalize_manifest(manifest_path: Path, output_dir: Path | None = None) -> IngestSummary:
    manifest = load_manifest(manifest_path)
    final_output_dir = output_dir or default_output_dir()
    total_sections = 0

    for track in manifest["tracks"]:
        document = build_normalized_document(manifest, track, manifest_path)
        write_document(final_output_dir, document)
        total_sections += document["stats"]["section_count"]

    return IngestSummary(
        output_dir=final_output_dir / manifest["artist_id"],
        total_tracks=len(manifest["tracks"]),
        total_sections=total_sections,
    )
