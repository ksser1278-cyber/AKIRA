# scripts/production/run_autonomous_calibration.py
"""Block L2: Self-Calibration (Autonomous 24h Sprint).

Analyzes RC results and adjusts creative policies to optimize
for the production 'Sweet Spot' (Quality vs. Novelty).
"""

from __future__ import annotations

import json
import sys
import io
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.akira_engine.creative.config import CreativeConfig


def calibrate():
    report_path = PROJECT_ROOT / "outputs" / "rc20_stabilization_report.json"
    if not report_path.exists():
        print("[CALIBRATION] No report found. Skipping.")
        return

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    results = report.get("details", [])
    if not results:
        print("[CALIBRATION] Empty report. Skipping.")
        return

    # 1. Tally Reasons
    reason_counts = {}
    for r in results:
        for reason in r.get("reasons", []):
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    total = len(results)
    print(f"[CALIBRATION] Analyzing {total} tracks...")
    for k, v in reason_counts.items():
        print(f"  - {k}: {v} ({v/total:.1%})")

    # 2. Heuristic Calibration
    config = CreativeConfig.load_canonical(PROJECT_ROOT)
    updates = {}

    # Logic A: Originality vs. Novelty
    orig_fail_rate = reason_counts.get("low_originality", 0) / total
    if orig_fail_rate > 0.4:
        # Too strict! Either the engine isn't creative enough or the bar is too high.
        # We lower the bar slightly to allow for more 'grounded' tracks.
        current = config.get("min_originality_composite")
        new_val = max(0.4, current - 0.05)
        if new_val != current:
            updates["min_originality_composite"] = new_val
            print(f"[AUTO-TUNE] Lowering min_originality: {current} -> {new_val}")

    # Logic B: Craft Score
    craft_fail_rate = reason_counts.get("low_craft_score", 0) / total
    if craft_fail_rate > 0.25:
        current = config.get("min_craft_score")
        new_val = max(60.0, current - 2.0)
        if new_val != current:
            updates["min_craft_score"] = new_val
            print(f"[AUTO-TUNE] Lowering min_craft: {current} -> {new_val}")

    # 3. Apply Updates
    if updates:
        for k, v in updates.items():
            config.set(k, v)
        print(f"[CALIBRATION] Policy updated: {updates}")
    else:
        print("[CALIBRATION] No adjustments needed. Thresholds stable.")


if __name__ == "__main__":
    calibrate()
