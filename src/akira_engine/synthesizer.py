from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Any
from dataclasses import dataclass

@dataclass
class SynthesisRequest:
    brief_path: Path
    artist_id: str
    target_model: str = "gemini-1.5-pro" # default to a high-reasoning model for artistic tasks

class LyricSynthesizer:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def parse_brief(self, brief_content: str) -> dict[str, Any]:
        """Extractions key sections and constraints from the generated MD brief."""
        data = {}
        
        # Extract Style of Music
        style_match = re.search(r"## Style of Music\s+```\s+(.*?)\s+```", brief_content, re.DOTALL)
        data["style_of_music"] = style_match.group(1).strip() if style_match else ""
        
        # Extract Song-Level Context (Phase 7)
        context_match = re.search(r"## Song-Level Context\s+(.*?)\s+## Lyrics Blueprint", brief_content, re.DOTALL)
        data["song_context"] = context_match.group(1).strip() if context_match else ""

        # Extract Lyrics Blueprint
        blueprint_match = re.search(r"## Lyrics Blueprint\s+(.*?)\s+## Generation Notes", brief_content, re.DOTALL)
        if blueprint_match:
            blueprint_text = blueprint_match.group(1).strip()
            # Extract section instructions
            sections = []
            for line in blueprint_text.splitlines():
                if line.startswith("- `"):
                    sections.append(line.strip())
            data["sections"] = sections
            
            # Extract metadata headers [Style: ...] [Vocal: ...]
            headers = re.findall(r"\[(Style|Vocal): (.*?)\]", blueprint_text)
            data["headers"] = [f"[{h[0]}: {h[1]}]" for h in headers]

        # Extract Generation Notes
        notes_match = re.search(r"## Generation Notes\s+(.*)", brief_content, re.DOTALL)
        if notes_match:
            data["notes"] = notes_match.group(1).strip()
            
        return data

    def build_system_prompt(self, brief_data: dict[str, Any], artist_id: str, nuances: dict[str, Any] | None = None) -> str:
        """Constructs a prompt for the LLM to act as a professional songwriter."""
        
        prompt = [
            f"You are a professional Japanese songwriter specializing in the {artist_id} style.",
            "Your task is to write high-fidelity Japanese lyrics based on a technical blueprint.",
            "\n### SONG-LEVEL CONTEXT & LOGIC",
            brief_data.get("song_context", "No additional context.")
        ]

        if nuances:
            prompt.append("\n### ARTISTIC NUANCES & STYLISTIC FLAVOR")
            if "representative_sabotage_examples" in nuances:
                examples = ", ".join(nuances["representative_sabotage_examples"])
                prompt.append(f"REPRESENTATIVE SABOTAGE EXAMPLES (to ground concepts): {examples}")
            if "potential_percussive_triggers" in nuances:
                triggers = ", ".join(nuances["potential_percussive_triggers"])
                prompt.append(f"POTENTIAL PERCUSSIVE TRIGGERS (for rhythm): {triggers}")
            
            prompt.append("\n### PHRASING & RHYTHMIC PRINCIPLES")
            markers = ", ".join(nuances.get("markers", []))
            prompt.append(f"PREFERRED MARKERS: {markers}")
            for principle in nuances.get("principles", []):
                prompt.append(f"- {principle}")
            
            if "entropy_instruction" in nuances:
                prompt.append(f"\n### CREATIVE ENTROPY\n- {nuances['entropy_instruction']}")
            if "experimental_freedom" in nuances:
                prompt.append(f"\n### EXPERIMENTAL FREEDOM\n- {nuances['experimental_freedom']}")

        prompt.extend([
            "\n### TECHNICAL CONSTRAINTS",
            f"MUSIC STYLE: {brief_data.get('style_of_music')}",
            "\n### ARTIST-SPECIFIC HEADERS (MANDATORY)",
            "CRITICAL: You MUST include the following two header lines at the VERY TOP of your output, verbatim:",
            "\n".join(brief_data.get("headers", [])),
            "\n### SECTION BLUEPRINT (Follow rhythm and goal strictly)",
            "\n".join(brief_data.get("sections", [])),
            "\n### WRITING PRINCIPLES & NEGATIVE CONSTRAINTS",
            brief_data.get("notes", ""),
            "\n### OUTPUT FORMAT",
            "1. First 2 lines: The mandatory headers [Style: ...] and [Vocal: ...].",
            "2. Next: The Markdown title line: '# [Track ID] Lyrics'.",
            "3. Body: Japanese lyrics with [Section Name] headers (e.g., [Verse 1], [Chorus]).",
            "Do not provide explanations, translations, or any introductory/concluding chatter."
        ])
        
        return "\n".join(prompt)

    def prepare_request_record(self, artist_id: str, track_id: str, brief_content: str, profile_data: dict[str, Any]) -> dict[str, Any]:
        """Prepares a single JSONL record for the gemini_songwriter infrastructure."""
        brief_data = self.parse_brief(brief_content)
        
        # Phase 8: Support both old and new nuance keys for robust transition
        nuances = profile_data.get("lyric_rules", {}).get("stylistic_nuances") or \
                  profile_data.get("lyric_rules", {}).get("rhythmic_nuances") or \
                  profile_data.get("lyric_rules", {}).get("grammar_guidelines")
        
        system_prompt = self.build_system_prompt(brief_data, artist_id, nuances)
        user_prompt = f"Write the lyrics for the track '{track_id}' based on the provided technical blueprint and artist persona."
        
        return {
            "request_id": f"synthesis_{artist_id}_{track_id}",
            "track_id": track_id,
            "artist_id": artist_id,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "output_contract": {
                "format": "markdown_section"
            }
        }

    def save_lyrics(self, artist_id: str, track_id: str, lyrics_text: str) -> Path:
        """Saves the generated lyrics to the outputs directory."""
        output_dir = self.project_root / "outputs" / "lyrics" / artist_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"{track_id}.lyrics.md"
        output_path.write_text(lyrics_text, encoding="utf-8")
        return output_path
