import os
import sys
import json
from pathlib import Path

# Add src to path for akira_engine imports
sys.path.append(str(Path("src").resolve()))

from akira_engine.japanese_lyric_features import build_markdown_japanese_profile, mora_unit_estimate

# Force UTF-8 for console output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# CONFIGURATION
INPUT_FILE = Path("datasets/corpus/alexandria_10k_raw.jsonl")
OUTPUT_FILE = Path("datasets/corpus/alexandria_10k_refined.jsonl")

def auto_section_lyrics(title, lyrics_raw):
    """
    High-Fidelity Structural DNA Detection.
    Identifies Verse (A-Melo), Pre-Chorus (B-Melo), and Chorus (Sabi) based on:
    1. Line length variance (Short lines often indicate B-Melo)
    2. Repetition patterns (Chorus lines often repeat or are longer/more energetic)
    3. Character density shifts.
    """
    lines = [line.strip() for line in lyrics_raw.splitlines() if line.strip()]
    if not lines: return ""

    # 1. Existing Header Respect
    has_headers = any(line.startswith("[") and line.endswith("]") for line in lines)
    if has_headers: return "\n".join(lines)

    # 2. Structural DNA Detection
    mora_counts = [mora_unit_estimate(line) for line in lines]
    avg_mora = sum(mora_counts) / len(mora_counts)
    
    sections = []
    current_section = []
    
    # Heuristic for J-Pop (8-line A, 4-line B, 8/16-line Chorus)
    # We'll split when we detect a significant "beat" change or every 8 lines as a fallback.
    for i, line in enumerate(lines):
        current_section.append(line)
        
        # Split criteria:
        # A. Next line is significantly different in length (Potential B-Melo/Chorus entry)
        # B. We've reached 8 lines (Standard A-Melo/Sabi block)
        should_split = False
        if i < len(lines) - 1:
            curr_len = mora_counts[i]
            next_len = mora_counts[i+1]
            if abs(curr_len - next_len) > 5 and len(current_section) >= 2:
                should_split = True
        
        if len(current_section) >= 8: should_split = True
        
        if should_split or i == len(lines) - 1:
            # Type classification
            sec_len = len(current_section)
            sec_avg_mora = sum(mora_unit_estimate(l) for l in current_section) / sec_len
            
            # Simple slotting: Intro -> Verse -> Pre-Chorus -> Chorus -> Outro
            sec_type = "Verse"
            if len(sections) == 0: sec_type = "Intro"
            elif sec_len <= 4 and sec_avg_mora < avg_mora: sec_type = "Pre-Chorus"
            elif sec_avg_mora > avg_mora: sec_type = "Chorus"
            
            # If Chorus is long, it might be a double Chorus
            if sec_type == "Chorus" and len(sections) > 0 and sections[-1].startswith("[Chorus]"):
                sec_type = "Bridge"
            
            sections.append(f"[{sec_type}]")
            sections.extend(current_section)
            sections.append("")
            current_section = []

    # 3. Final slotting: First Chorus as 'Sabi', Last as 'Dai-Sabi' is handled by the profile builder
    return "\n".join(sections)

def main():
    if not INPUT_FILE.exists():
        print(f"Input file {INPUT_FILE} not found.")
        return

    print(f"Starting Alexandria Structural Refinement (Phase 2)...")
    
    count = 0
    refined_count = 0
    
    with INPUT_FILE.open("r", encoding="utf-8") as f_in, OUTPUT_FILE.open("w", encoding="utf-8") as f_out:
        for line in f_in:
            count += 1
            try:
                record = json.loads(line)
                title = record.get("title", "Unknown")
                raw_lyrics = record.get("lyrics", "")
                
                # Apply high-fidelity sectioning
                refined_lyrics = auto_section_lyrics(title, raw_lyrics)
                
                # Capture structural features using engine
                try:
                    profile = build_markdown_japanese_profile(title, refined_lyrics)
                    record["structural_profile"] = profile
                except Exception:
                    record["structural_profile"] = None
                
                record["lyrics"] = refined_lyrics
                record["refined_on"] = "2026-03-30"
                
                f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                refined_count += 1
                
                if refined_count % 100 == 0:
                    print(f"    [OK] Refined {refined_count} tracks...")
                    
            except Exception as e:
                print(f"    [SKIP] Error processing record {count}: {e}")

    print(f"\nRefinement Completed. Total Refined: {refined_count}/{count}")

if __name__ == "__main__":
    main()
