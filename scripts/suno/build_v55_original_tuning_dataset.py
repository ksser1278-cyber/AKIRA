import os
import json
from pathlib import Path

# The exact group allocations (Artists) agreed upon
groups = {
    "Model_A_Dark_Subculture": ["maretu", "pinocchiop", "kairiki_bear", "hiragi_kirai", "maresuke", "nilfruits", "kikuo"],
    "Model_B_Emotional_Pop": ["ado", "deco27", "hachi", "balloon", "eve", "tsumiki", "nuyuri", "kanaria", "orangestar", "honeyworks", "ryo_supercell", "mikitop"],
    "Model_C_Urban_Night": ["giga", "syudou", "chinozo", "yurrycanon", "kuragep", "neru", "magnetite", "iyowa", "police_piccadilly", "ayase", "teniwoha", "kemu", "wowaka", "niki", "sasakure_uk"]
}

def clean_lyric_sections(sections):
    lines = []
    for sec in sections:
        # e.g., '[Verse 1]'
        header = f"[{sec.get('section_name', sec.get('section_type', 'Verse'))}]"
        lines.append(header)
        for line in sec.get("lines", []):
            lines.append(line.strip())
        lines.append("") # space between sections
    return "\n".join(lines).strip()

def extract_style_prompt(cond_dict):
    tags = []
    for k in ["genre_anchors", "tempo_feels", "vocal_tones", "production_palette", "energy_arc", "imagery_anchors"]:
        items = cond_dict.get(k, [])
        if isinstance(items, list):
            tags.extend(items)
        elif isinstance(items, str):
            tags.append(items)
            
    if not tags:
         # fallback generic
         tags = ["J-Pop", "Vocaloid", "Fast Tempo"]
         
    return "[Style: " + ", ".join(tags) + "]"

def build_datasets():
    data_dir = Path("data")
    output_dir = Path("outputs") / "suno_v55_custom_models"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Store records by title to deduplicate
    extracted_records = {}

    for root, dirs, files in os.walk(data_dir):
        for name in files:
            if not name.endswith(".json"):
                continue
                
            path = Path(root) / name
            try:
                with path.open(encoding="utf-8") as f:
                    content = json.load(f)
                    
                if not isinstance(content, dict):
                    continue
                    
                tid = content.get("track_identity", {})
                if not tid:
                    continue
                    
                artist = (tid.get("artist") or tid.get("artist_name") or "")
                title = tid.get("title", "")
                
                # Deduplication by title
                if title in extracted_records:
                    continue
                    
                # We need lyrics and prompt formatting
                lyrics_sections = content.get("lyric_ground_truth", {}).get("sections", [])
                if not lyrics_sections:
                    continue # Skip instrumentals/bad data
                    
                lyrics_text = clean_lyric_sections(lyrics_sections)
                style_prompt = extract_style_prompt(content.get("prompt_conditioning", {}))
                
                extracted_records[title] = {
                    "metadata": {"artist": artist, "title": title},
                    "suno_prompt": style_prompt,
                    "lyrics": lyrics_text
                }
            except Exception:
                pass

    # Allocate to groups and write JSONL
    allocations = {g: [] for g in groups.keys()}
    
    for title, record in extracted_records.items():
        artist_lower = record["metadata"]["artist"].lower()
        
        assigned = False
        for g_name, g_artists in groups.items():
            if any(a in artist_lower for a in g_artists) and len(allocations[g_name]) < 24:
                allocations[g_name].append(record)
                assigned = True
                break
                
        # Handle loose tracks if any group needs filling
        if not assigned:
             if len(allocations["Model_B_Emotional_Pop"]) < 24:
                 allocations["Model_B_Emotional_Pop"].append(record)
             elif len(allocations["Model_C_Urban_Night"]) < 24:
                 allocations["Model_C_Urban_Night"].append(record)

    print("Extraction Summary:")
    for g_name, records in allocations.items():
        # Write to JSONL
        out_path = output_dir / f"{g_name}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"- {g_name}.jsonl: {len(records)} tracks")
        
        # Write readable Markdown bundle report
        md_path = output_dir / f"{g_name}_Report.md"
        with md_path.open("w", encoding="utf-8") as md:
            md.write(f"# {g_name} - Suno v5.5 Custom Model Training Data\n")
            md.write(f"Total Tracks: {len(records)}/24\n\n")
            for i, r in enumerate(records, 1):
                md.write(f"## {i}. {r['metadata']['artist']} - {r['metadata']['title']}\n\n")
                md.write(f"**Style Prompt:**\n`{r['suno_prompt']}`\n\n")
                md.write("**Lyrics:**\n```text\n")
                md.write(f"{r['lyrics']}\n```\n\n")

if __name__ == "__main__":
    build_datasets()
