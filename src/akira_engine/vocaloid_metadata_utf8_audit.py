from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _contains_replacement_char(value: str) -> bool:
    return "\ufffd" in value


def _contains_control_noise(value: str) -> bool:
    for char in value:
        codepoint = ord(char)
        if codepoint < 32 and char not in "\t\n\r":
            return True
    return False


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        collected: list[str] = []
        for item in value:
            collected.extend(_walk_strings(item))
        return collected
    if isinstance(value, dict):
        collected: list[str] = []
        for item in value.values():
            collected.extend(_walk_strings(item))
        return collected
    return []


def audit_vocaloid_metadata_utf8(*, corpus_root: Path, output_root: Path) -> dict[str, Any]:
    corpus_root = corpus_root.resolve()
    output_root = output_root.resolve()
    accepted_dir = corpus_root / "accepted"

    clean_records: list[dict[str, Any]] = []
    flagged_records: list[dict[str, Any]] = []

    for path in sorted(accepted_dir.glob("vocadb_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        strings = _walk_strings(payload)
        flags: list[str] = []
        if any(_contains_replacement_char(value) for value in strings):
            flags.append("text:replacement_char")
        if any(_contains_control_noise(value) for value in strings):
            flags.append("text:control_noise")

        row = {
            "track_id": _safe_text(payload.get("track_identity", {}).get("track_id")),
            "canonical_title": _safe_text(payload.get("track_identity", {}).get("canonical_title")),
            "path": str(path),
            "flags": flags,
        }
        if flags:
            flagged_records.append(row)
        else:
            clean_records.append(row)

    manifest = {
        "schema_version": "1.0",
        "record_type": "vocaloid_metadata_utf8_audit",
        "corpus_root": str(corpus_root),
        "counts": {
            "records": len(clean_records) + len(flagged_records),
            "clean_records": len(clean_records),
            "flagged_records": len(flagged_records),
        },
        "clean_records": clean_records,
        "flagged_records": flagged_records,
    }
    manifest_path = write_json(output_root / "vocaloid_metadata_utf8_audit.json", manifest)
    manifest["manifest_path"] = str(manifest_path)

    lines = [
        "# Vocaloid Metadata UTF-8 Audit",
        "",
        f"- `records`: {manifest['counts']['records']}",
        f"- `clean_records`: {manifest['counts']['clean_records']}",
        f"- `flagged_records`: {manifest['counts']['flagged_records']}",
    ]
    if flagged_records:
        lines.extend(["", "## Flagged Records", ""])
        for row in flagged_records:
            lines.append(f"- `{row['track_id']}`: {', '.join(row['flags'])}")
    (output_root / "vocaloid_metadata_utf8_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest
