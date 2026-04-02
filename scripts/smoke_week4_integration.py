"""Integration Test: Week 4 - Hook Grammar Bank on Real Corpus.

Processes all 219 tracks, extracts hooks, and builds the global 
hook grammar bank with syllable patterns and rhyme statistics.
"""

import sys
import io
import json
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # scripts/ -> AKIRA ENGINE
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.akira_engine.corpus_intelligence.hooks.mod import build_hook_bank_index

def run_integration_test():
    print("===========================================================")
    print("  AKIRA ENGINE - Week 4 Integration: Hook Grammar Bank")
    print("===========================================================")

    # 1. Look for conditioning records
    conditioning_paths = list(PROJECT_ROOT.glob("data/**/*.conditioning.json"))
    print(f"Found {len(conditioning_paths)} conditioning files.")
    
    records = []
    for p in conditioning_paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                records.append(json.load(f))
        except:
            continue

    if not records:
        print("Error: No conditioning records found!")
        return

    # 2. Build bank index
    output_path = PROJECT_ROOT / "data" / "hooks" / "hook_grammar_bank_v1.json"
    result = build_hook_bank_index(
        records,
        output_path=output_path
    )

    print(f"\nBuild Results:")
    print(f" - Output: {result['output_path']}")
    print(f" - Total Hooks Analyzed: {result['total_hooks']}")
    print(f" - Top Pattern: {result['top_pattern']}")

    # 3. Analyze Bank Contents
    with open(output_path, "r", encoding="utf-8") as f:
        bank_data = json.load(f)

    # Top Patterns
    print("\nTop 10 Syllable Patterns (Mora Counts):")
    for p in bank_data.get("top_patterns", [])[:10]:
        print(f" - {p['pattern']}: {p['count']} hooks ({p['ratio']:.2%})")

    # Exclamations / Repetition stats
    stats = bank_data.get("exclamations", {})
    print("\nRepetition/Structure Distribution:")
    for rep, count in stats.items():
        print(f" - {rep}: {count} ({count/result['total_hooks']:.2%})")

    print("\nIntegration test complete!")

if __name__ == "__main__":
    run_integration_test()
