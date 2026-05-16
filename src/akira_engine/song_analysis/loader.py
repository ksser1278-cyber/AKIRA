from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def load_inputs(input_dir: Path) -> dict[str, Any]:
    final_input_dir = input_dir.resolve()
    song_input = read_json(final_input_dir / "song_input.json")
    if not isinstance(song_input, dict):
        fallback = read_json(final_input_dir / "song_meta.json")
        if isinstance(fallback, dict):
            song_input = fallback
    if not isinstance(song_input, dict):
        raise FileNotFoundError(f"Missing song_input.json or song_meta.json in {final_input_dir}")

    lyrics_path = final_input_dir / "lyrics.txt"
    if not lyrics_path.exists():
        raise FileNotFoundError(f"Missing lyrics.txt in {final_input_dir}")

    return {
        "input_dir": str(final_input_dir),
        "song_input": song_input,
        "lyrics": lyrics_path.read_text(encoding="utf-8"),
        "timeline_manual": read_json(final_input_dir / "timeline_manual.json", default=None),
        "audio_features": read_json(final_input_dir / "audio_features.json", default=None),
        "transcript": read_json(final_input_dir / "transcript.json", default=None),
    }
