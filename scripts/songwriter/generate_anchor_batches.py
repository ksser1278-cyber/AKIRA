from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.akira_engine.generator import GenerationRequest, generate_package

def run_anchor_benchmark(artist_id: str, anchor_file_path: Path):
    print(f"Starting anchor benchmark for: {artist_id}")
    
    if not anchor_file_path.exists():
        print(f"Error: Anchor file not found at {anchor_file_path}")
        return

    data = json.loads(anchor_file_path.read_text(encoding="utf-8"))
    anchor_set = data.get("anchor_set", [])
    
    artist_profile_path = Path("artists") / artist_id / "profile.json"
    if not artist_profile_path.exists():
        print(f"Error: Artist profile not found at {artist_profile_path}")
        return

    output_base_dir = Path("outputs") / "benchmarks" / artist_id
    output_base_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    for entry in anchor_set:
        req_id = entry.get("id", "unknown")
        print(f"  Generating {req_id}: {entry['theme']}...")
        
        request = GenerationRequest(
            artist_file=artist_profile_path,
            mode_id=entry["mode_id"],
            theme=entry["theme"],
            emotion=entry["emotion"],
            narrative=entry["narrative"],
            keywords=entry.get("keywords"),
            output_path=output_base_dir / f"{req_id}_{entry['mode_id']}.md"
        )
        
        try:
            generate_package(request)
            success_count += 1
        except Exception as e:
            print(f"    [ERROR] Failed to generate {req_id}: {e}")

    print(f"\nBenchmark completed for {artist_id}:")
    print(f"  Total requests: {len(anchor_set)}")
    print(f"  Successfully generated: {success_count}")
    print(f"  Results saved to: {output_base_dir}")

if __name__ == "__main__":
    # PinocchioP
    run_anchor_benchmark(
        "pinocchiop", 
        Path("artists/pinocchiop/anchor_set.json")
    )
    
    print("-" * 40)
    
    # DECO*27
    run_anchor_benchmark(
        "deco27", 
        Path("artists/deco27/anchor_set.json")
    )
