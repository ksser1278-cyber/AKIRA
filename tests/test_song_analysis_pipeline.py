from __future__ import annotations

import json
from pathlib import Path

from src.akira_engine.song_analysis import (
    match_song_analysis_lyrics,
    materialize_song_analysis_inputs_from_metadata,
    run_song_analysis_pipeline,
    write_song_analysis_template,
)
from src.akira_engine.song_analysis.validator import validate_claim


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_song_analysis_pipeline_writes_all_outputs(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    write_json(
        input_dir / "song_input.json",
        {
            "song_id": "demo_song",
            "title": "どきどき",
            "artist": "test",
            "language": "ja",
            "known_metadata": {"lyricist": "test", "composer": "test", "genre": "POP"},
            "available_sources": {"lyrics": True, "audio": False},
        },
    )
    (input_dir / "lyrics.txt").write_text(
        "\n".join(
            [
                "[Intro]",
                "どきどき",
                "ズキズキ",
                "[Chorus]",
                "君だけ もっと",
                "どきどき",
            ]
        ),
        encoding="utf-8",
    )

    manifest = run_song_analysis_pipeline(input_dir=input_dir, output_dir=tmp_path / "out")

    assert manifest["ok"] is True
    output_paths = manifest["output_paths"]
    for key in (
        "pass_1_identity",
        "pass_2_lyrics",
        "pass_3_timeline",
        "pass_4_music_hooks",
        "pass_5_recipe",
        "human_report",
        "ai_reconstruction",
    ):
        assert Path(output_paths[key]).exists()

    pass_2 = json.loads(Path(output_paths["pass_2_lyrics"]).read_text(encoding="utf-8"))
    line_count = sum(len(section["lines"]) for section in pass_2["sections"])
    assert line_count == 4


def test_song_analysis_template_writer(tmp_path: Path) -> None:
    result = write_song_analysis_template(output_dir=tmp_path / "template", song_id="template_song")

    assert Path(result["paths"]["song_input"]).exists()
    assert Path(result["paths"]["lyrics"]).exists()


def test_inferred_claim_requires_evidence() -> None:
    errors = validate_claim(
        {
            "choice": "x",
            "reason": "y",
            "effect": "z",
            "reuse_method": "r",
            "status": "INFERRED",
            "confidence": 0.5,
            "evidence": [],
        },
        location="claim",
    )

    assert "claim: inferred or hypothesis claim must include evidence" in errors


def test_materialize_metadata_creates_song_analysis_package(tmp_path: Path) -> None:
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    write_json(
        metadata_dir / "vocadb_100.json",
        {
            "schema_version": "1.0",
            "record_type": "vocaloid_metadata_record",
            "track_identity": {"track_id": "vocadb_100", "canonical_title": "Demo Song"},
            "canonical_basis": {"is_vocaloid_canonical": True, "inclusion_basis": "vocadb_canonical"},
            "vocal_synthesis": {"engine_family": "vocaloid", "voicebanks": ["Hatsune Miku"]},
            "credits": {"producer": "Demo Producer", "lyricist": "", "composer": "", "arranger": ""},
            "release_context": {"original_platform": "youtube", "original_upload_date": "2026-01-01"},
            "metadata_sources": [
                {"label": "VocaDB song 100", "source_type": "vocadb", "url": "https://vocadb.net/S/100"},
                {"label": "Original upload", "source_type": "official_upload", "url": "https://youtu.be/demo"},
            ],
            "collection_status": {"metadata_quality": "seed", "canonical_review_status": "needs_review"},
        },
    )

    manifest = materialize_song_analysis_inputs_from_metadata(
        metadata_dir=metadata_dir,
        output_root=tmp_path / "packages",
    )

    package_dir = tmp_path / "packages" / "vocadb_100"
    assert manifest["counts"]["materialized"] == 1
    assert manifest["counts"]["ready_for_analysis"] == 0
    assert (package_dir / "song_input.json").exists()
    assert (package_dir / "lyrics.todo.txt").exists()
    assert not (package_dir / "lyrics.txt").exists()


def test_materialize_metadata_attaches_local_lyrics(tmp_path: Path) -> None:
    metadata_dir = tmp_path / "metadata"
    lyrics_root = tmp_path / "lyrics"
    metadata_dir.mkdir()
    lyrics_root.mkdir()
    write_json(
        metadata_dir / "vocadb_101.json",
        {
            "schema_version": "1.0",
            "record_type": "vocaloid_metadata_record",
            "track_identity": {"track_id": "vocadb_101", "canonical_title": "Local Lyric Song"},
            "canonical_basis": {"is_vocaloid_canonical": True, "inclusion_basis": "vocadb_canonical"},
            "vocal_synthesis": {"engine_family": "vocaloid", "voicebanks": ["Hatsune Miku"]},
            "credits": {"producer": "Demo Producer", "lyricist": "", "composer": "", "arranger": ""},
            "release_context": {"original_platform": "youtube", "original_upload_date": "2026-01-01"},
            "metadata_sources": [
                {"label": "VocaDB song 101", "source_type": "vocadb", "url": "https://vocadb.net/S/101"}
            ],
            "collection_status": {"metadata_quality": "seed", "canonical_review_status": "needs_review"},
        },
    )
    (lyrics_root / "vocadb_101.txt").write_text("[Intro]\nla la\n", encoding="utf-8")

    manifest = materialize_song_analysis_inputs_from_metadata(
        metadata_dir=metadata_dir,
        output_root=tmp_path / "packages",
        lyrics_root=lyrics_root,
    )

    package_dir = tmp_path / "packages" / "vocadb_101"
    assert manifest["counts"]["ready_for_analysis"] == 1
    assert (package_dir / "lyrics.txt").read_text(encoding="utf-8").strip() == "[Intro]\nla la"
    song_input = json.loads((package_dir / "song_input.json").read_text(encoding="utf-8"))
    assert song_input["available_sources"]["lyrics"] is True
    source_manifest = json.loads((package_dir / "source_manifest.json").read_text(encoding="utf-8"))
    assert source_manifest["lyric_match_status"] == "matched"


def test_match_lyrics_reports_unmatched_and_matched_files(tmp_path: Path) -> None:
    metadata_dir = tmp_path / "metadata"
    lyrics_root = tmp_path / "lyrics"
    metadata_dir.mkdir()
    lyrics_root.mkdir()
    write_json(
        metadata_dir / "vocadb_102.json",
        {
            "schema_version": "1.0",
            "record_type": "vocaloid_metadata_record",
            "track_identity": {"track_id": "vocadb_102", "canonical_title": "Report Song"},
            "canonical_basis": {"is_vocaloid_canonical": True, "inclusion_basis": "vocadb_canonical"},
            "vocal_synthesis": {"engine_family": "vocaloid", "voicebanks": ["Hatsune Miku"]},
            "credits": {"producer": "Demo Producer", "lyricist": "", "composer": "", "arranger": ""},
            "release_context": {"original_platform": "youtube", "original_upload_date": "2026-01-01"},
            "metadata_sources": [
                {"label": "VocaDB song 102", "source_type": "vocadb", "url": "https://vocadb.net/S/102"}
            ],
            "collection_status": {"metadata_quality": "seed", "canonical_review_status": "needs_review"},
        },
    )
    (lyrics_root / "vocadb_102.txt").write_text("matched\n", encoding="utf-8")
    (lyrics_root / "unused.txt").write_text("unused\n", encoding="utf-8")

    report = match_song_analysis_lyrics(
        metadata_dir=metadata_dir,
        lyrics_root=lyrics_root,
        output_root=tmp_path / "match",
    )

    assert report["counts"]["matched"] == 1
    assert report["counts"]["unmatched_lyrics"] == 1
    assert Path(report["outputs"]["json_path"]).exists()
    assert Path(report["outputs"]["md_path"]).exists()


def test_materialize_does_not_attach_ambiguous_title_match(tmp_path: Path) -> None:
    metadata_dir = tmp_path / "metadata"
    lyrics_root = tmp_path / "lyrics"
    metadata_dir.mkdir()
    lyrics_root.mkdir()
    for track_id in ("vocadb_201", "vocadb_202"):
        write_json(
            metadata_dir / f"{track_id}.json",
            {
                "schema_version": "1.0",
                "record_type": "vocaloid_metadata_record",
                "track_identity": {"track_id": track_id, "canonical_title": "Same Title"},
                "canonical_basis": {"is_vocaloid_canonical": True, "inclusion_basis": "vocadb_canonical"},
                "vocal_synthesis": {"engine_family": "vocaloid", "voicebanks": ["Hatsune Miku"]},
                "credits": {"producer": "Demo Producer", "lyricist": "", "composer": "", "arranger": ""},
                "release_context": {"original_platform": "youtube", "original_upload_date": "2026-01-01"},
                "metadata_sources": [
                    {"label": track_id, "source_type": "vocadb", "url": f"https://vocadb.net/S/{track_id}"}
                ],
                "collection_status": {"metadata_quality": "seed", "canonical_review_status": "needs_review"},
            },
        )
    (lyrics_root / "Same Title.txt").write_text("ambiguous\n", encoding="utf-8")

    manifest = materialize_song_analysis_inputs_from_metadata(
        metadata_dir=metadata_dir,
        output_root=tmp_path / "packages",
        lyrics_root=lyrics_root,
    )

    assert manifest["lyrics_match_counts"]["ambiguous"] == 2
    assert manifest["counts"]["ready_for_analysis"] == 0
    assert not (tmp_path / "packages" / "vocadb_201" / "lyrics.txt").exists()
    source_manifest = json.loads(
        (tmp_path / "packages" / "vocadb_201" / "source_manifest.json").read_text(encoding="utf-8")
    )
    assert source_manifest["lyric_match_status"] == "ambiguous"
