# scripts/production/run_stabilization_rc20.py
"""Phase 3: RC-20 Revalidation (Stabilization Sprint).

Runs 20 autonomous production slots using the new CreativeRunner.
Verifies that stabilization policies (originality, diversity) are active.
"""

from __future__ import annotations

import json
import sys
import io
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.akira_engine.creative.runner import CreativeRunner


def main():
    runner = CreativeRunner(PROJECT_ROOT)
    
    # 20-track RC matrix
    workload = [
        {"artist": "pinocchiop", "mode": "dark_cute_breakdown", "count": 2},
        {"artist": "pinocchiop", "mode": "energetic_pop", "count": 2},
        {"artist": "kanaria", "mode": "dark_cute_breakdown", "count": 4},
        {"artist": "maretu", "mode": "dark_cute_breakdown", "count": 4},
        {"artist": "hachi", "mode": "default", "count": 4},
        {"artist": "ado", "mode": "energetic_pop", "count": 4},
    ]
    
    results = []
    total_start = time.time()
    
    print(f"=== RC-20 Stabilization Revalidation ===")
    print(f"Target: 20 tracks via CreativeRunner")
    print(f"Enforcing: Originality >= 0.5, Cluster Quota <= 25%, Hook Continuity <= 3")
    print("="*50)

    for item in workload:
        artist = item["artist"]
        mode = item["mode"]
        for i in range(item["count"]):
            print(f"\n[RC] Running {artist} ({mode}) {i+1}/{item['count']}...")
            try:
                # Set creativity index based on index to explore diversity
                creativity = 0.4 + (i * 0.15)
                
                res = runner.run_full_cycle(
                    artist_id=artist,
                    mode_id=mode,
                    candidate_count=2, # Reduced for RC speed
                    creativity_index=min(0.9, creativity)
                )
                
                results.append({
                    "ok": True,
                    "artist": artist,
                    "mode": mode,
                    "track_id": res["track_id"],
                    "status": res["admission"]["status"].value,
                    "reasons": res["admission"]["reasons"],
                    "grade": res["grade"]
                })
                print(f"  [OK] Status: {res['admission']['status'].value}, Grade: {res['grade']}")
                if res["admission"]["reasons"]:
                    print(f"  [NOTES] {res['admission']['reasons']}")
            except Exception as e:
                print(f"  [ERROR] Failed: {e}")
                results.append({
                    "ok": False,
                    "artist": artist,
                    "mode": mode,
                    "error": str(e)
                })

    duration = time.time() - total_start
    
    # Summary
    admitted = [r for r in results if r.get("status") in ("pass", "warn")]
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": duration,
        "total": len(results),
        "admitted_count": len(admitted),
        "admission_rate": len(admitted) / len(results) if results else 0,
        "details": results
    }
    
    out_path = PROJECT_ROOT / "outputs" / "rc20_stabilization_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        
    print("\n" + "="*50)
    print(f"RC-20 Stabilization Complete ({duration:.1f}s)")
    print(f"Admitted: {len(admitted)}/{len(results)} ({summary['admission_rate']:.1%})")
    print(f"Report: {out_path}")
    print("="*50)


if __name__ == "__main__":
    main()
