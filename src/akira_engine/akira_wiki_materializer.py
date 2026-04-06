from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json, write_jsonl


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _slug(text: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in _safe_text(text))
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "unknown"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _wiki_page_meta(
    *,
    page_id: str,
    page_type: str,
    title: str,
    track_ids: list[str],
    producer_ids: list[str],
    voicebank_ids: list[str],
    mode_ids: list[str],
    source_paths: list[str],
    wiki_links: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "record_type": "akira_wiki_page",
        "page_id": page_id,
        "page_type": page_type,
        "title": title,
        "track_ids": track_ids,
        "producer_ids": producer_ids,
        "voicebank_ids": voicebank_ids,
        "mode_ids": mode_ids,
        "source_paths": source_paths,
        "wiki_links": wiki_links,
    }


def _write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _track_markdown(
    *,
    metadata: dict[str, Any],
    generation: dict[str, Any] | None,
    readiness: dict[str, Any] | None,
) -> str:
    identity = metadata.get("track_identity", {})
    credits = metadata.get("credits", {})
    vocal = metadata.get("vocal_synthesis", {})
    release = metadata.get("release_context", {})
    collection = metadata.get("collection_status", {})

    title = _safe_text(identity.get("canonical_title"))
    producer = _safe_text(credits.get("producer")) or "unknown"
    voicebanks = ", ".join(vocal.get("voicebanks", []) or ["unknown"])
    value_tier = _safe_text(collection.get("corpus_value_tier")) or "unclassified"
    original_platform = _safe_text(release.get("original_platform")) or "unknown"
    original_upload_date = _safe_text(release.get("original_upload_date")) or "unknown"

    readiness_lines = ["- no readiness record"]
    if readiness:
        readiness_lines = [
            f"- quality level: `{_safe_text(readiness.get('quality_level'))}`",
            f"- joinable: `{readiness.get('joinable', False)}`",
            f"- prompt ready: `{readiness.get('prompt_ready', False)}`",
            f"- production candidate: `{readiness.get('production_candidate', False)}`",
            f"- professional target: `{readiness.get('professional_target', False)}`",
        ]
        reasons = readiness.get("reasons", [])
        if reasons:
            readiness_lines.append(f"- blocking reasons: {', '.join(reasons)}")

    lyric_lines = ["- no lyric profile"]
    sound_lines = ["- no sound profile"]
    if generation:
        lyric = generation.get("lyric_profile", {})
        sound = generation.get("sound_profile", {})
        lyric_lines = [
            f"- section behavior: {', '.join(lyric.get('section_behavior', [])[:6]) or 'none'}",
            f"- hook behavior: {', '.join(lyric.get('hook_behavior', [])[:6]) or 'none'}",
            f"- imagery bank: {', '.join(lyric.get('imagery_bank', [])[:8]) or 'none'}",
        ]
        sound_lines = [
            f"- groove profile: {', '.join(sound.get('groove_profile', [])[:6]) or 'none'}",
            f"- arrangement profile: {', '.join(sound.get('arrangement_profile', [])[:6]) or 'none'}",
            f"- texture profile: {', '.join(sound.get('texture_profile', [])[:6]) or 'none'}",
            f"- positive anchors: {', '.join(sound.get('sound_anchors', {}).get('positive', [])[:8]) or 'none'}",
        ]

    sources = metadata.get("metadata_sources", [])
    source_lines = [
        f"- [{_safe_text(item.get('label'))}]({_safe_text(item.get('url'))})"
        for item in sources
        if _safe_text(item.get("url"))
    ] or ["- none"]

    return "\n".join(
        [
            f"# {title}",
            "",
            "## Identity",
            "",
            f"- track id: `{_safe_text(identity.get('track_id'))}`",
            f"- producer: `{producer}`",
            f"- voicebanks: `{voicebanks}`",
            f"- corpus value tier: `{value_tier}`",
            f"- original platform: `{original_platform}`",
            f"- original upload date: `{original_upload_date}`",
            "",
            "## Generation Readiness",
            "",
            *readiness_lines,
            "",
            "## Lyric Profile",
            "",
            *lyric_lines,
            "",
            "## Sound Profile",
            "",
            *sound_lines,
            "",
            "## Sources",
            "",
            *source_lines,
        ]
    )


def materialize_akira_wiki(
    *,
    canonical_corpus_root: Path,
    generation_root: Path,
    readiness_manifest_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    canonical_corpus_root = canonical_corpus_root.resolve()
    generation_root = generation_root.resolve()
    readiness_manifest_path = readiness_manifest_path.resolve()
    output_root = output_root.resolve()

    accepted_dir = canonical_corpus_root / "accepted"
    tracks_dir = output_root / "tracks"
    overview_dir = output_root / "overview"
    meta_dir = output_root / "_meta"
    tracks_dir.mkdir(parents=True, exist_ok=True)
    overview_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    generation_records = {
        path.stem: _load_json(path)
        for path in (generation_root / "records").glob("*.json")
    }
    readiness_manifest = _load_json(readiness_manifest_path)
    readiness_by_track = {
        _safe_text(item.get("track_id")): item
        for item in readiness_manifest.get("records", [])
        if _safe_text(item.get("track_id"))
    }

    page_meta: list[dict[str, Any]] = []
    professional_tracks: list[str] = []
    prompt_ready_tracks: list[str] = []
    total_tracks = 0

    for metadata_path in sorted(accepted_dir.glob("vocadb_*.json")):
        metadata = _load_json(metadata_path)
        track_id = _safe_text(metadata.get("track_identity", {}).get("track_id")) or metadata_path.stem
        generation = generation_records.get(track_id)
        readiness = readiness_by_track.get(track_id)
        title = _safe_text(metadata.get("track_identity", {}).get("canonical_title")) or track_id
        producer = _safe_text(metadata.get("credits", {}).get("producer"))
        producer_slug = _slug(producer)
        voicebanks = metadata.get("vocal_synthesis", {}).get("voicebanks", []) or []
        voicebank_slugs = [_slug(value) for value in voicebanks if _safe_text(value)]

        page_path = tracks_dir / f"{track_id}.md"
        _write_markdown(page_path, _track_markdown(metadata=metadata, generation=generation, readiness=readiness))
        page_meta.append(
            _wiki_page_meta(
                page_id=track_id,
                page_type="track",
                title=title,
                track_ids=[track_id],
                producer_ids=[producer_slug],
                voicebank_ids=voicebank_slugs,
                mode_ids=[],
                source_paths=[str(metadata_path)],
                wiki_links=[str(page_path)],
            )
        )
        total_tracks += 1
        if readiness and readiness.get("professional_target"):
            professional_tracks.append(track_id)
        if readiness and readiness.get("prompt_ready"):
            prompt_ready_tracks.append(track_id)

    _write_markdown(
        overview_dir / "corpus-status.md",
        "\n".join(
            [
                "# Corpus Status",
                "",
                f"- total canonical tracks in wiki: `{total_tracks}`",
                f"- prompt-ready tracks: `{len(prompt_ready_tracks)}`",
                f"- professional-target tracks: `{len(professional_tracks)}`",
            ]
        ),
    )
    _write_markdown(
        overview_dir / "generation-readiness.md",
        "\n".join(
            [
                "# Generation Readiness",
                "",
                f"- prompt-ready tracks: `{len(prompt_ready_tracks)}`",
                f"- professional-target tracks: `{len(professional_tracks)}`",
                "",
                "## Professional Target Tracks",
                "",
                *([f"- `{track_id}`" for track_id in professional_tracks] or ["- none"]),
            ]
        ),
    )

    meta_jsonl_path = write_jsonl(meta_dir / "akira_wiki_pages.jsonl", page_meta)
    manifest = {
        "schema_version": "1.0",
        "record_type": "akira_wiki_materialization_manifest",
        "inputs": {
            "canonical_corpus_root": str(canonical_corpus_root),
            "generation_root": str(generation_root),
            "readiness_manifest_path": str(readiness_manifest_path),
        },
        "counts": {
            "track_pages": total_tracks,
            "prompt_ready_tracks": len(prompt_ready_tracks),
            "professional_target_tracks": len(professional_tracks),
        },
        "outputs": {
            "wiki_root": str(output_root),
            "tracks_dir": str(tracks_dir),
            "meta_jsonl": str(meta_jsonl_path),
        },
    }
    manifest_path = write_json(output_root / "_meta" / "akira_wiki_materialization_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
