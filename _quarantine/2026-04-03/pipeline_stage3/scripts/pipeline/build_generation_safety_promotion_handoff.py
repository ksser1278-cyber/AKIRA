from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.generation_safety_promotion_handoff import (
    build_promotion_handoff,
    render_promotion_batch_prompt,
    render_promotion_handoff_markdown,
)


def main() -> None:
    payload = build_promotion_handoff(PROJECT_ROOT)

    planning_dir = PROJECT_ROOT / "reports" / "planning"
    planning_dir.mkdir(parents=True, exist_ok=True)
    (planning_dir / "generation_safety_promotion_handoff.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (planning_dir / "generation_safety_promotion_handoff.md").write_text(
        render_promotion_handoff_markdown(payload),
        encoding="utf-8",
    )

    handoff_root = PROJECT_ROOT / "data" / "_global" / "generation_safety_promotion"
    handoff_root.mkdir(parents=True, exist_ok=True)
    (handoff_root / "batch_delegation_prompt.txt").write_text(
        render_promotion_batch_prompt(payload),
        encoding="utf-8",
    )

    for artist in payload.get("artists", []):
        artist_dir = handoff_root / artist["artist_id"]
        artist_dir.mkdir(parents=True, exist_ok=True)
        (artist_dir / "incoming").mkdir(parents=True, exist_ok=True)
        artist_payload = {
            "schema_version": payload.get("schema_version", "1.0"),
            "record_type": "generation_safety_promotion_artist_packet",
            "artist_id": artist["artist_id"],
            "track_count": artist["track_count"],
            "tracks": artist["tracks"],
        }
        (artist_dir / "packet.json").write_text(
            json.dumps(artist_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        packet_lines = [
            f"# {artist['artist_id']} Promotion Packet",
            "",
            f"- track_count `{artist['track_count']}`",
            "",
        ]
        for track in artist.get("tracks", []):
            blockers = ", ".join(track.get("blockers", [])) or "none"
            packet_lines.append(
                f"- `{track['track_id']}` / score `{track['score']}` / blockers `{blockers}` / path `{track['path']}`"
            )
        (artist_dir / "packet.md").write_text("\n".join(packet_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
