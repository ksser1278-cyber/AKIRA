import os
import sys
import json
import time
from pathlib import Path

# Force UTF-8 for console output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import yt_dlp
except ImportError:
    print("yt-dlp missing. Please install it.")
    exit(1)

# STAGE 1: Hyper-Consistent PURE VOCALOID Artist Pools
# Human vocalists (Ado, Eve, Tuyu, etc.) are strictly REMOVED.
groups = {
    "Model_A_Dark_Subculture": [
        "maretu", "pinocchiop", "kairiki_bear", "hiragi_kirai", "hiiragi_kirai", 
        "nilfruits", "kikuo", "atols", "ezfg", "surii", "dazibee", "cosmo", "baker"
    ],
    "Model_B_Emotional_Pop": [
        "deco27", "hachi", "tsumiki", "nuyuri", "kanaria", 
        "balloon", "orangestar", "honeyworks", "mikitop", 
        "nanou", "keeno", "40mp", "scop", "harumaki_gohan", "jin", "last_note"
    ],
    "Model_C_Urban_Night": [
        "giga", "syudou", "chinozo", "yurrycanon", "kuragep", "neru", 
        "magnetite", "iyowa", "police_piccadilly", "ayase", "teniwoha", 
        "kemu", "wowaka", "niki", "sasakure_uk", "vivinos"
    ]
}

# Known synth voice markers
known_synths = ["miku", "gumi", "rin", "len", "luka", "meiko", "kaito", "flower", "ia", "teto", "yukari", "guna", "vocaloid", "cevio", "voicevox", "utau", "synthv"]
human_voices = ["ado", "eve", "arufa", "tuyu", "reol", "majiko", "soraru", "mafumafu", "96neko", "luz", "daoko"]

# STAGE 2: Aesthetic & Vocaloid Filter
def extract_tags(cond_dict):
    tags = []
    for k in ["genre_anchors", "tempo_feels", "vocal_tones", "production_palette", "energy_arc", "imagery_anchors"]:
        items = cond_dict.get(k, [])
        if isinstance(items, list):
            tags.extend(items)
        elif isinstance(items, str):
            tags.append(items)
    return tags

def is_pure_vocaloid(content):
    # 1. Check Vocal Metadata directly
    vocalists = content.get("track_identity", {}).get("credits", {}).get("vocal", [])
    if vocalists:
        is_synth = False
        has_human = False
        for v in vocalists:
            vname = v.get("name", "").lower()
            if any(s in vname for s in known_synths):
                is_synth = True
            if any(h in vname for h in human_voices):
                has_human = True
        
        # We need AT LEAST a synth, and absolutely NO known humans (for purity)
        if is_synth and not has_human:
            return True
    
    # 2. Fallback to Genre Tags
    lower_tags = " ".join([t.lower() for t in extract_tags(content.get("prompt_conditioning", {}))])
    if "vocaloid" in lower_tags and not any(h in lower_tags for h in human_voices):
        return True
        
    return False

def matches_aesthetic_filter(model_name, tags):
    lower_tags = " ".join([t.lower() for t in tags])
    
    if model_name == "Model_A_Dark_Subculture":
        if any(x in lower_tags for x in ["acoustic", "ballad", "soft"]):
             return False
        core = ["industrial", "glitch", "heavy bass", "fast tempo", "dark", "repetitive", "screaming", "vocaloid"]
        return any(c in lower_tags for c in core)
        
    elif model_name == "Model_B_Emotional_Pop":
        if any(x in lower_tags for x in ["club", "chill", "minimal"]):
             return False
        core = ["rock", "guitar", "cinematic", "high range", "emotional", "band", "power", "aggressive", "j-pop", "shouting", "high-tension"]
        return any(c in lower_tags for c in core)
        
    elif model_name == "Model_C_Urban_Night":
        if any(x in lower_tags for x in ["acoustic", "ballad"]):
             return False
        core = ["edm", "synth", "driving", "dance", "heavy bass drop", "club", "urban", "night", "neon", "retro"]
        return any(c in lower_tags for c in core)
        
    return True

def clean_lyric_sections(sections):
    lines = []
    for sec in sections:
        header = f"[{sec.get('section_name', sec.get('section_type', 'Verse'))}]"
        lines.append(header)
        for line in sec.get("lines", []):
            lines.append(line.strip())
        lines.append("")
    return "\n".join(lines).strip()

def gather_pure_vocaloid():
    data_dir = Path("data")
    all_tracks = []
    seen = set()
    
    # Massive Globbing
    for path in data_dir.glob("**/reference_tracks/*.json"):
        try:
            with path.open(encoding="utf-8") as f:
                content = json.load(f)
            tid = content.get("track_identity", {})
            if not tid: continue
            
            title = tid.get("title", "")
            if not title or title in seen: continue
            
            # PURE VOCALOID CHECK
            if not is_pure_vocaloid(content):
                continue
            
            artist_raw = (tid.get("artist") or tid.get("artist_name") or tid.get("track_id", "").split("_")[0] or "").lower()
            lyrics = content.get("lyric_ground_truth", {}).get("sections", [])
            if not lyrics: continue
            
            raw_tags = extract_tags(content.get("prompt_conditioning", {}))
            sources = content.get("source_provenance", {}).get("lyric_sources", [])
            url = next((s.get("url") for s in sources if "youtu" in s.get("url", "")), None)
            
            all_tracks.append({
                "metadata": {"artist": artist_raw, "title": title},
                "raw_tags": raw_tags,
                "suno_prompt": "[Style: " + ", ".join(raw_tags) + "]",
                "lyrics": clean_lyric_sections(lyrics),
                "url": url
            })
            seen.add(title)
        except Exception: pass
    return all_tracks

def final_pure_vocaloid_sync():
    all_tracks = gather_pure_vocaloid()
    bundle_dir = Path("outputs/suno_v55_custom_models")
    bundle_dir.mkdir(parents=True, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'extract_audio': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    for model_name, artist_list in groups.items():
        print(f"\n======================\nPure Vocaloid Filtering {model_name}\n======================")
        audio_dir = bundle_dir / f"{model_name}_Audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Filter by artist & strict filter
        valid_candidates = [c for c in all_tracks if any(a in c["metadata"]["artist"] for a in artist_list)]
        valid_candidates = [c for c in valid_candidates if matches_aesthetic_filter(model_name, c["raw_tags"])]
        
        print(f" -> Pool Scan identified {len(valid_candidates)} pure Vocaloid tracks.")
        
        valid_prefixes = []
        valid_records = []
        
        for cand in valid_candidates:
            title = cand["metadata"]["title"]
            artist = cand["metadata"]["artist"]
            clean_title = "".join(x for x in title if x.isalnum() or x in " -_")
            clean_artist = "".join(x for x in artist if x.isalnum() or x in " -_")
            prefix = f"{clean_artist}_{clean_title}_ref"
            valid_prefixes.append(prefix)
            
            # Check if file exists
            if list(audio_dir.glob(f"{prefix}.*")):
                valid_records.append(cand)
            else:
                ydl_opts["outtmpl"] = str(audio_dir / prefix) + ".%(ext)s"
                print(f"  [DL] {artist} - {title}")
                try:
                    search_query = cand["url"] if cand["url"] else f"ytsearch1:{artist} {title} vocaloid"
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([search_query])
                    valid_records.append(cand)
                    time.sleep(1)
                except Exception: pass

        # PURGE OUTLIERS (Including all previous human tracks)
        for f in audio_dir.glob("*_ref.*"):
            if f.stem not in valid_prefixes:
                os.remove(f)
        
        # Save JSONL
        print(f" -> Finalizing {model_name} with {len(valid_records)} pure Vocaloid tracks!")
        jsonl_path = bundle_dir / f"{model_name}.jsonl"
        with jsonl_path.open("w", encoding="utf-8") as f:
             for cand in valid_records:
                 export_obj = {
                     "metadata": cand["metadata"],
                     "suno_prompt": cand["suno_prompt"],
                     "lyrics": cand["lyrics"]
                 }
                 f.write(json.dumps(export_obj, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    final_pure_vocaloid_sync()
