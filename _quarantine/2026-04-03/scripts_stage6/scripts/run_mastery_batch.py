import json
import time
import os
import sys
import io
from pathlib import Path
from typing import List, Dict, Any, Optional

# Force UTF-8 for console output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add 'src' to sys.path for direct imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from akira_engine.songwriter_v2 import run_songwriter_v2
from akira_engine.mastery_linter import lint_mastery_output

CORPUS_PATH = Path("datasets/corpus/alexandria_10k_elite_refined.jsonl")
OUTPUT_ROOT = Path("outputs/production_v2_5")
STATE_PATH = Path("data/mastery/batch_state.json")

# Genre Routing Mapping (Elite Cohort)
CORE_STYLE_ROUTING = {
    "maretu": "dark_cute_breakdown",
    "wowaka": "glitch_hyper_pop",
    "deco*27": "anthemic_cinematic",
    "pinocchiop": "glitch_hyper_pop",
    "neru": "glitch_hyper_pop",
    "syudou": "dark_cute_breakdown",
    "kairiki bear": "dark_cute_breakdown",
    "chinozo": "anthemic_cinematic",
    "hachi": "hachi_classic",
    "nilfruits": "royal_minimalist",
}

class MasteryBatchRunner:
    def __init__(self, limit: int = 100):
        self.limit = limit
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if STATE_PATH.exists():
            try:
                return json.loads(STATE_PATH.read_text(encoding="utf-8"))
            except:
                pass
        return {"processed_ids": [], "failed_ids": [], "completed_count": 0}

    def _save_state(self):
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def _resolve_mode(self, track: Dict[str, Any]) -> str:
        artist_lower = track.get("artist", "").lower()
        for key, mode in CORE_STYLE_ROUTING.items():
            if key in artist_lower:
                return mode
        return "universal"

    def run_batch(self):
        print(f"--- Starting Elite Mastery Synthesis Batch (V2.5) ---")
        
        if not CORPUS_PATH.exists():
            print(f"Error: Corpus not found at {CORPUS_PATH}")
            return

        with open(CORPUS_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Selection of tracks that haven't been processed yet
        to_process = []
        for l in lines:
            try:
                track = json.loads(l)
                t_id = str(track.get("id"))
                if t_id not in self.state["processed_ids"]:
                    to_process.append(track)
            except: continue
        
        print(f"Total remain in cohort: {len(to_process)}. Batch limit: {self.limit}")
        
        count = 0
        for track in to_process:
            if count >= self.limit: break
            
            t_id = str(track.get("id"))
            mode = self._resolve_mode(track)
            track_name = track.get("title", "Untitled")
            
            print(f"\n[{count+1}/{self.limit}] Generating: {track_name} (ID: {t_id}, Mode: {mode})")
            
            try:
                # Execution
                # Note: songwriter_v2 expects source_jsonl and track_id
                result = run_songwriter_v2(
                    source_jsonl=CORPUS_PATH,
                    track_id=t_id,
                    output_dir=OUTPUT_ROOT / t_id,
                    candidate_count=3,  # Set to 3 for higher quality chance
                    include_history=False
                )
                
                if result:
                    # Extract the mastery_alignment score from the winning candidate
                    # The critic_results are sorted, so the first one is the winner
                    winner = result.get("critic_results")[0]
                    # We want the 'mastery_alignment' specifically
                    mastery_score = winner.get("scores", {}).get("mastery_alignment", 0.0)
                    
                    # Linter Check
                    markdown = ""
                    # Load the generated lyric
                    lyric_file = OUTPUT_ROOT / t_id / "selected_lyric.md"
                    if lyric_file.exists():
                        markdown = lyric_file.read_text(encoding="utf-8")
                        
                    lint = lint_mastery_output(markdown, mode_id=mode)
                    
                    final_data = {
                        "v2_5_id": f"v2_5_{t_id}",
                        "source_track_id": t_id,
                        "title": track_name,
                        "artist": track.get("artist"),
                        "mode": mode,
                        "mastery_score": mastery_score,
                        "total_engine_score": result.get("selected_score", 0.0),
                        "lint_result": lint,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                    }
                    
                    (OUTPUT_ROOT / t_id / "mastery_v2_5_data.json").write_text(json.dumps(final_data, indent=2), encoding="utf-8")
                    
                    self.state["processed_ids"].append(t_id)
                    self.state["completed_count"] += 1
                    count += 1
                    print(f"  [OK] Mastery: {mastery_score:.3f} | Total: {result.get('selected_score')} | Lint: {lint['is_valid']}")
                else:
                    self.state["failed_ids"].append(t_id)
                    print(f"  [FAIL] No result returned")
                    
            except Exception as e:
                print(f"  [ERROR] {e}")
                self.state["failed_ids"].append(t_id)
                
            self._save_state()
            time.sleep(1) # Rate limit padding

        print(f"\n--- Batch Process Complete ---")
        print(f"Total Successfully Processed: {self.state['completed_count']}")

if __name__ == "__main__":
    # Test batch of 5 to verify pipeline
    runner = MasteryBatchRunner(limit=5)
    runner.run_batch()

if __name__ == "__main__":
    # Test batch of 5 to verify pipeline
    runner = MasteryBatchRunner(limit=5)
    runner.run_batch()
