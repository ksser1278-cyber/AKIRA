import json
import re
import time
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.akira_engine.web_scrape import build_requests_session, fetch_html

def discover_lyric_urls(records_dir: Path, output_map_path: Path):
    session = build_requests_session("AKIRA-ENGINE/1.0 lyric-discovery-a100")
    records = sorted(records_dir.glob("*.json"))
    url_map = {}
    
    # Priority domains
    DOMAINS = ["utaten.com", "uta-net.com", "petitlyrics.com", "lyrical-nonsense.com"]
    
    print(f"Starting discovery for {len(records)} tracks...")
    
    for i, record_path in enumerate(records):
        with open(record_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        track_id = data["track_identity"]["track_id"]
        vocadb_url = data["acquisition_sources"]["vocadb_pages"][0]
        
        print(f"[{i+1}/{len(records)}] Checking {track_id} -> {vocadb_url}")
        
        try:
            # Respectful delay
            time.sleep(1.5)
            html = fetch_html(session, vocadb_url, timeout_seconds=15)
            
            discovered_url = None
            site_preset = "auto"
            
            # Simple regex search for lyric links in the VocaDB page
            # Usually they are in the 'External links' section
            for domain in DOMAINS:
                match = re.search(fr'href="(https?://(?:www\.)?{re.escape(domain)}/[^"]+)"', html)
                if match:
                    discovered_url = match.group(1)
                    site_preset = domain.split(".")[0]
                    break
            
            if discovered_url:
                url_map[track_id] = {
                    "lyric_url": discovered_url,
                    "site_preset": site_preset,
                    "label": f"Discovered from VocaDB ({site_preset})"
                }
                print(f"  FOUND: {discovered_url}")
            else:
                print(f"  NOT FOUND.")
                
        except Exception as e:
            print(f"  ERROR: {e}")
            
    with open(output_map_path, "w", encoding="utf-8") as f:
        json.dump(url_map, f, indent=2, ensure_ascii=False)
        
    return len(url_map)

if __name__ == "__main__":
    records_dir = Path("C:/JPop_Songwriter/AKIRA ENGINE/datasets/training/lyric_technique_acquisition_queue/batch_a100/records")
    output_map = Path("C:/JPop_Songwriter/AKIRA ENGINE/datasets/training/lyric_technique_acquisition_queue/batch_a100/url_map_a100.json")
    count = discover_lyric_urls(records_dir, output_map)
    print(f"Discovery complete. Found {count} lyric URLs.")
