from __future__ import annotations

from pathlib import Path
from typing import Any

from .loader import load_inputs, write_json, write_text
from .passes import (
    analyze_composition_arrangement_hooks,
    analyze_identity_and_core_intent,
    analyze_lyrics_line_by_line,
    analyze_timeline_sections,
    build_integrated_songwriting_recipe,
)
from .report_builder import build_ai_reconstruction_json, build_human_report
from .schema import EvidenceStatus
from .validator import validate_outputs


def _verify_metadata(raw_data: dict[str, Any]) -> dict[str, Any]:
    song_input = raw_data["song_input"]
    known_metadata = song_input.get("known_metadata", {}) if isinstance(song_input.get("known_metadata"), dict) else {}
    verified: dict[str, Any] = {}
    for key, value in known_metadata.items():
        verified[key] = {
            "value": value,
            "status": EvidenceStatus.VERIFIED.value,
            "confidence": 1.0,
            "evidence": ["song_input.known_metadata"],
        }
    for key in ("title", "artist", "vocal", "url", "language"):
        if song_input.get(key) and key not in verified:
            verified[key] = {
                "value": song_input[key],
                "status": EvidenceStatus.VERIFIED.value,
                "confidence": 0.95,
                "evidence": [f"song_input.{key}"],
            }
    return verified


def default_output_dir(input_dir: Path, song_id: str) -> Path:
    return input_dir.resolve() / "outputs" / song_id


def run_song_analysis_pipeline(*, input_dir: Path, output_dir: Path | None = None) -> dict[str, Any]:
    raw_data = load_inputs(input_dir)
    song_id = str(raw_data["song_input"].get("song_id") or "unknown_song")
    final_output_dir = (output_dir.resolve() if output_dir else default_output_dir(input_dir, song_id))

    verified_data = _verify_metadata(raw_data)
    pass_1 = analyze_identity_and_core_intent(raw_data, verified_data)
    pass_2 = analyze_lyrics_line_by_line(raw_data["lyrics"], pass_1)
    pass_3 = analyze_timeline_sections(raw_data.get("timeline_manual"), pass_2, pass_1)
    pass_4 = analyze_composition_arrangement_hooks(raw_data.get("audio_features"), pass_2, pass_3)
    pass_5 = build_integrated_songwriting_recipe(pass_1, pass_2, pass_3, pass_4)

    partial_outputs = {
        "pass_1": pass_1,
        "pass_2": pass_2,
        "pass_3": pass_3,
        "pass_4": pass_4,
        "pass_5": pass_5,
    }
    validation_report = validate_outputs(partial_outputs)
    ai_reconstruction = build_ai_reconstruction_json(
        pass_1=pass_1,
        pass_2=pass_2,
        pass_3=pass_3,
        pass_4=pass_4,
        pass_5=pass_5,
        validation_report=validation_report,
    )
    human_report = build_human_report(
        pass_1=pass_1,
        pass_2=pass_2,
        pass_3=pass_3,
        pass_4=pass_4,
        pass_5=pass_5,
        validation_report=validation_report,
    )

    final_outputs = {
        **partial_outputs,
        "validation_report": validation_report,
        "human_report": human_report,
        "ai_reconstruction": ai_reconstruction,
    }
    final_validation = validate_outputs(final_outputs)
    final_outputs["validation_report"] = final_validation
    human_report = build_human_report(
        pass_1=pass_1,
        pass_2=pass_2,
        pass_3=pass_3,
        pass_4=pass_4,
        pass_5=pass_5,
        validation_report=final_validation,
    )
    ai_reconstruction = build_ai_reconstruction_json(
        pass_1=pass_1,
        pass_2=pass_2,
        pass_3=pass_3,
        pass_4=pass_4,
        pass_5=pass_5,
        validation_report=final_validation,
    )

    output_paths = {
        "pass_1_identity": str(write_json(final_output_dir / "pass_1_identity.json", pass_1)),
        "pass_2_lyrics": str(write_json(final_output_dir / "pass_2_lyrics.json", pass_2)),
        "pass_3_timeline": str(write_json(final_output_dir / "pass_3_timeline.json", pass_3)),
        "pass_4_music_hooks": str(write_json(final_output_dir / "pass_4_music_hooks.json", pass_4)),
        "pass_5_recipe": str(write_json(final_output_dir / "pass_5_recipe.json", pass_5)),
        "validation_report": str(write_json(final_output_dir / "validation_report.json", final_validation)),
        "human_report": str(write_text(final_output_dir / "human_report.md", human_report)),
        "ai_reconstruction": str(write_json(final_output_dir / "ai_reconstruction.json", ai_reconstruction)),
    }

    manifest = {
        "schema_version": "1.0",
        "record_type": "song_analysis_run_manifest",
        "song_id": song_id,
        "input_dir": str(input_dir.resolve()),
        "output_dir": str(final_output_dir),
        "ok": final_validation["ok"],
        "output_paths": output_paths,
        "validation_summary": final_validation.get("summary", {}),
        "validation_errors": final_validation.get("errors", []),
    }
    manifest_path = write_json(final_output_dir / "run_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def write_song_analysis_template(*, output_dir: Path, song_id: str = "sample_song") -> dict[str, Any]:
    final_output_dir = output_dir.resolve()
    final_output_dir.mkdir(parents=True, exist_ok=True)
    song_input = {
        "song_id": song_id,
        "title": "Sample Title",
        "artist": "Sample Artist",
        "vocal": "",
        "url": "",
        "language": "ja",
        "analysis_goal": [
            "songwriting_intent",
            "composition_intent",
            "hook_design",
            "ai_reconstruction",
        ],
        "known_metadata": {
            "lyricist": "",
            "composer": "",
            "arranger": [],
            "release_date": "",
            "genre": "",
        },
        "available_sources": {
            "lyrics": True,
            "audio": False,
            "mv": False,
            "official_commentary": False,
            "instrumental": False,
        },
    }
    timeline = {
        "timeline": [
            {
                "time_range": {"start": "0:00", "end": "0:10"},
                "section": "Intro",
                "lyric_event": "opening phrase introduces the song's memory object",
                "composition_event": "short vocal cell preview",
                "arrangement_event": "minimal setup before the main section",
                "energy_level": 5,
                "vocal_density": 5,
                "instrument_density": 5,
                "probable_intent": "Let the listener identify the hook surface before the full premise.",
                "listener_effect": "The opening feels immediately repeatable.",
                "status": EvidenceStatus.HYPOTHESIS.value,
                "confidence": 0.5,
            }
        ]
    }
    audio_features = {
        "bpm": None,
        "key": "",
        "chord_notes": "",
        "section_markers": [],
    }
    paths = {
        "song_input": str(write_json(final_output_dir / "song_input.json", song_input)),
        "lyrics": str(
            write_text(
                final_output_dir / "lyrics.txt",
                "[Intro]\nどきどき\nズキズキ\n\n[Chorus]\n君だけ もっと\nどきどき\n",
            )
        ),
        "timeline_manual": str(write_json(final_output_dir / "timeline_manual.json", timeline)),
        "audio_features": str(write_json(final_output_dir / "audio_features.json", audio_features)),
    }
    return {"input_dir": str(final_output_dir), "paths": paths}
