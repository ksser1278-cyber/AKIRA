import os
import sys
import json
from pathlib import Path

# Add src to path for akira_engine imports
sys.path.append(str(Path("src").resolve()))
from akira_engine.japanese_lyric_features import build_markdown_japanese_profile, mora_unit_estimate

# Force UTF-8 for console output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

INPUT_FILE = Path("datasets/corpus/alexandria_10k_elite_push.jsonl")
OUTPUT_FILE = Path("datasets/corpus/alexandria_10k_elite_refined.jsonl")

def auto_section_lyrics(title, lyrics_raw):
    lines = [line.strip() for line in lyrics_raw.splitlines() if line.strip()]
    if not lines: return ""
    mora_counts = [mora_unit_estimate(line) for line in lines]
    avg_mora = sum(mora_counts) / len(mora_counts) if mora_counts else 0
    sections = []
    current_section = []
    for i, line in enumerate(lines):
        current_section.append(line)
        should_split = False
        if i < len(lines) - 1:
            if abs(mora_counts[i] - mora_counts[i+1]) > 5 and len(current_section) >= 2:
                should_split = True
        if len(current_section) >= 8: should_split = True
        if should_split or i == len(lines) - 1:
            sec_len = len(current_section)
            sec_avg_mora = sum(mora_unit_estimate(l) for l in current_section) / sec_len
            sec_type = "Verse"
            if len(sections) == 0: sec_type = "Intro"
            elif sec_len <= 4 and sec_avg_mora < avg_mora: sec_type = "Pre-Chorus"
            elif sec_avg_mora > avg_mora: sec_type = "Chorus"
            sections.append(f"[{sec_type}]")
            sections.extend(current_section)
            sections.append("")
            current_section = []
    return "\n".join(sections)

def main():
    if not INPUT_FILE.exists():
        print("Input file not found.")
        return

    print("Refining Elite Push records with structural profiles...")
    
    refined_count = 0
    with INPUT_FILE.open("r", encoding="utf-8") as f_in, OUTPUT_FILE.open("w", encoding="utf-8") as f_out:
        for line in f_in:
            try:
                record = json.loads(line)
                title = record.get("title", "Unknown")
                raw_lyrics = record.get("lyrics", "")
                
                # Structural DNA Detection
                refined_lyrics = auto_section_lyrics(title, raw_lyrics)
                profile = build_markdown_japanese_profile(title, refined_lyrics)
                
                record["lyrics"] = refined_lyrics
                record["structural_profile"] = profile
                record["refined_on"] = "2026-03-30"
                record["source"] = "elite_push"
                
                f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                refined_count += 1
                if refined_count % 50 == 0:
                    print(f"    [OK] Refined {refined_count} tracks...")
                    
            except Exception as e:
                print(f"    [SKIP] Error: {e}")

    print(f"Refinement Complete. Total: {refined_count}")

if __name__ == "__main__":
    main()
