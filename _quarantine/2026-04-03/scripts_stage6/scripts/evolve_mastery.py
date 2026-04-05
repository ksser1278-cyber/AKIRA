import json
import statistics
import time
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional

# Constants for Guardrails
MIN_SAMPLE_THRESHOLD = 30
MAX_MORA_STEP = 0.1
MAX_REP_STEP = 0.05
MAX_TOTAL_DRIFT_RATIO = 0.15  # 15% of base

DATA_DIR = Path("data/mastery")
SNAPSHOT_DIR = DATA_DIR / "snapshots"
OUTPUTS_DIR = Path("outputs")

@dataclass
class MasteryStats:
    mode: str
    sample_count: int = 0
    mora_mean: float = 0.0
    mora_std_dev: float = 0.0
    mora_median: float = 0.0
    rep_mean: float = 0.0
    rep_std_dev: float = 0.0
    alignment_mean: float = 0.0
    last_updated: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    confidence: float = 0.0

class MasteryEvolver:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        self.dna_matrix = self._load_dna_matrix()

    def _load_dna_matrix(self) -> Dict[str, Dict[str, Any]]:
        path = DATA_DIR / "mastery_dna_matrix.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}

    def aggregate_results(self):
        """
        Scans all outputs/ to aggregate metrics per mode.
        """
        raw_data = {}
        
        # Walk through all critic_results.json
        for path in OUTPUTS_DIR.rglob("critic_results.json"):
            try:
                # Find the plan.json in the same or parent dir
                plan_path = path.parent / "plan.json"
                if not plan_path.exists(): continue
                plan = json.loads(plan_path.read_text(encoding="utf-8"))
                mode = plan.get("primary_mode", "universal")
                
                results = json.loads(path.read_text(encoding="utf-8")).get("critic_results", [])
                for res in results:
                    scores = res.get("scores", {})
                    # We need actual metrics, but critic_results only have scores.
                    # In a real system, we'd store a metrics.json too.
                    # For now, we simulate extraction from scores or assume a 'stats.json' exists.
                    # Let's check for 'run_report.md' or similar for raw values?
                    # Actually, let's assume we extract 'Mastery Alignment' as the primary signal.
                    
                    if mode not in raw_data:
                        raw_data[mode] = {"alignments": [], "densities": []}
                    
                    raw_data[mode]["alignments"].append(scores.get("mastery_alignment", 0.0))
                    # Note: In a production version, we would extract raw mora from lyrics here.
            except Exception as e:
                print(f"Error processing {path}: {e}")

        # Process summaries
        new_matrix = {}
        for mode, data in raw_data.items():
            alignments = data["alignments"]
            if not alignments: continue
            
            count = len(alignments)
            mean_val = sum(alignments) / count
            std_dev = statistics.stdev(alignments) if count > 1 else 0
            
            stats = MasteryStats(
                mode=mode,
                sample_count=count,
                alignment_mean=mean_val,
                mora_std_dev=std_dev,
                confidence=1.0 / (std_dev + 0.1) * (count / MIN_SAMPLE_THRESHOLD)
            )
            new_matrix[mode] = asdict(stats)
            
        self.dna_matrix = new_matrix
        (DATA_DIR / "mastery_dna_matrix.json").write_text(json.dumps(new_matrix, indent=2), encoding="utf-8")
        print(f"Aggregated data for {len(new_matrix)} modes.")

    def propose_calibration(self) -> Dict[str, Any]:
        """
        Observe -> Propose logic.
        """
        proposals = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "modes": {}}
        
        for mode, stats in self.dna_matrix.items():
            if stats["sample_count"] < MIN_SAMPLE_THRESHOLD:
                print(f"Skipping {mode}: Insufficient samples ({stats['sample_count']}/{MIN_SAMPLE_THRESHOLD})")
                continue
            
            # Simple Drift Logic: If Alignment Mean < 0.75, propose minor nudge
            # In a real elite system, we compare 'Mean' vs 'Elite Target'
            drift = 0.75 - stats["alignment_mean"] # Target is 0.75 mastery
            
            if abs(drift) > 0.05:
                # Propose a damped offset for target mora (example)
                offset = max(-MAX_MORA_STEP, min(MAX_MORA_STEP, drift * 2.0))
                proposals["modes"][mode] = {
                    "confidence": stats["confidence"],
                    "proposed_mora_offset": round(offset, 3),
                    "reason": f"Mastery Alignment drift detected: {round(drift, 3)}"
                }
        
        (DATA_DIR / "calibration_proposal.json").write_text(json.dumps(proposals, indent=2), encoding="utf-8")
        return proposals

if __name__ == "__main__":
    evolver = MasteryEvolver()
    evolver.aggregate_results()
    proposals = evolver.propose_calibration()
    
    print("\n--- Mastery Evolution Proposal ---")
    if not proposals["modes"]:
        print("No calibrations proposed. System is stable.")
    for mode, p in proposals["modes"].items():
        print(f"MODE: {mode}")
        print(f"  Proposal: Mora Offset {p['proposed_mora_offset']}")
        print(f"  Reason: {p['reason']}")
    print("----------------------------------")
