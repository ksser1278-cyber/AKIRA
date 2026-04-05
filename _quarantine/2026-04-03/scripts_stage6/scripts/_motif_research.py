import json
import sys
import io

def analyze_conditioning(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            d = json.load(f)
        
        print(f"File: {file_path}")
        ident = d.get("track_identity")
        if isinstance(ident, dict):
            print(f"Song Title: {ident.get('title')}")
        else:
            # Maybe it's a string from my previous view
            print(f"Track Identity: {ident}")
            
        print("\nLyric Ground Truth Sections:")
        lgt = d.get("lyric_ground_truth", {})
        if isinstance(lgt, dict):
            for s in lgt.get("sections", []):
                name = s.get("section_name", "Unknown")
                lines = s.get("lines", [])
                print(f" - {name}: {lines[:1]}...")
        
        print("\nSection Analysis Vocabulary Focus:")
        sa = d.get("section_analysis", [])
        if isinstance(sa, list):
            for s in sa:
                name = s.get("section_name", "Unknown")
                vocab = s.get("vocabulary_focus", [])
                print(f" - {name}: {vocab}")

        print("\nSong Intent Motifs:")
        intent = d.get("song_intent", {})
        if isinstance(intent, dict):
            print(f" - Key Motifs: {intent.get('key_motifs', [])}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    analyze_conditioning('data/maretu/reference_tracks/brain_revolution_girl.conditioning.json')
