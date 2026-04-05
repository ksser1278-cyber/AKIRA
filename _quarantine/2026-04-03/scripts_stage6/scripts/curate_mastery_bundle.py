import json
import os
import sys
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any, Optional

QUOTA_PER_MODE = 20 # Up to 20 tracks per mode
MIN_MASTERY_SCORE = 0.75 # Lower limit for 'Elite' cohort
OUTPUT_ROOT = Path("outputs/production_v2_5")
CURATION_LOG = Path("data/mastery/selection_manifest.json")

class MasteryBundleCurator:
    def __init__(self, target_bundle_size: int = 100):
        self.target_size = target_bundle_size
        self.selected = []
        self.rejected = []
        self.mode_counts = Counter()

    def curate(self):
        print(f"--- Starting Diversity-Balanced Curation (Phase 6) ---")
        
        # 1. Collect all candidates
        candidates = []
        for path in OUTPUT_ROOT.rglob("mastery_v2_5_data.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                candidates.append(data)
            except: continue
        
        # 2. Tiered Sort (Mastery Score Primary)
        candidates.sort(key=lambda x: x.get("mastery_score", 0.0), reverse=True)
        print(f"Total candidates scanned: {len(candidates)}")

        # 3. Apply Gates
        for c in candidates:
            t_id = c.get("source_track_id")
            mode = c.get("mode", "universal")
            score = c.get("mastery_score", 0.0)
            lint = c.get("lint_result", {"is_valid": False})
            
            # 3A. Hard Fail Gate (Linter & Mastery)
            if not lint.get("is_valid"):
                c["reject_reason"] = f"Linter Failure: {', '.join(lint.get('reasons', []))}"
                self.rejected.append(c)
                continue
            
            if score < MIN_MASTERY_SCORE:
                c["reject_reason"] = f"Low Mastery Score: {score}"
                self.rejected.append(c)
                continue
                
            # 3B. Quota Gate (Diversity)
            if self.mode_counts[mode] >= QUOTA_PER_MODE:
                c["reject_reason"] = f"Mode Quota Filled: {mode} ({QUOTA_PER_MODE})"
                self.rejected.append(c)
                continue
            
            # 3C. Lexical Similarity Gate (Future improvement: actually diff the text)
            # For now, we block identical titles (Simple de-dupe)
            if any(s.get("title") == c.get("title") for s in self.selected):
                c["reject_reason"] = "Title Duplication"
                self.rejected.append(c)
                continue

            # Selection Success
            self.selected.append(c)
            self.mode_counts[mode] += 1
            
            if len(self.selected) >= self.target_size:
                break

        # 4. Save Selection Manifest
        manifest = {
            "version": "2.5.0",
            "curation_date": "2026-03-30T14:00:00Z",
            "summary": {
                "total_candidates": len(candidates),
                "total_selected": len(self.selected),
                "total_rejected": len(self.rejected),
                "mode_distribution": dict(self.mode_counts)
            },
            "selected_tracks": self.selected,
            "rejected_tracks": self.rejected
        }
        
        CURATION_LOG.parent.mkdir(parents=True, exist_ok=True)
        CURATION_LOG.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        
        print(f"\n--- Curation Complete ---")
        print(f"Selected: {len(self.selected)}")
        print(f"Rejected: {len(self.rejected)}")
        for mode, count in self.mode_counts.items():
            print(f"  {mode}: {count}")

if __name__ == "__main__":
    curator = MasteryBundleCurator(target_bundle_size=100)
    curator.curate()
