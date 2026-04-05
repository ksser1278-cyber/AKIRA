import json
from pathlib import Path
from akira_engine.songwriter_io import project_root
from akira_engine.songwriter_v2 import run_songwriter_v2

def compare_stylistic_pivots():
    # Use a known valid Maretu seed
    seed_path = project_root() / "data" / "maretu" / "reference_tracks" / "darling.conditioning.json"
    with open(seed_path, "r", encoding="utf-8") as f:
        base_record = json.load(f)
    
    pivots = [
        ("dark_cute_breakdown", "Dark Cute (High Density/Glitch)"),
        ("anthemic_cinematic", "Neo-Anthemic (Smooth/Heroic)")
    ]
    
    results = {}
    
    for mode_id, label in pivots:
        print(f"\n--- Generating: {label} ---")
        
        # Clone and modify
        target_record = json.loads(json.dumps(base_record))
        if "target" not in target_record: target_record["target"] = {}
        target_record["target"]["primary_mode"] = mode_id
        target_record["force_glitch_intensity"] = 0.5 if "dark" in mode_id else 0.05
        
        # Inject track_id to top level so choose_record finds it
        rectrack_id = target_record.get("track_identity", {}).get("track_id", "pivot_test")
        target_record["track_id"] = rectrack_id
        
        # Temporary seed for this run
        temp_dir = Path("outputs/pivot_test")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_jsonl = temp_dir / f"{mode_id}_seed.jsonl"
        temp_jsonl.write_text(json.dumps(target_record) + "\n", encoding="utf-8")
        
        # Extract track_id from identity
        current_track_id = target_record.get("track_identity", {}).get("track_id", "pivot_test")
        
        # Run engine
        run_songwriter_v2(
            source_jsonl=temp_jsonl,
            track_id=current_track_id,
            output_dir=temp_dir / mode_id,
            candidate_count=1
        )
        
        # Load results
        lyric_path = temp_dir / mode_id / "selected_lyric.md"
        results[mode_id] = lyric_path.read_text(encoding="utf-8")
        print(f"Done: {label}")

    # Save comparison report
    report_path = Path("outputs/pivot_test/comparison_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Stylistic Pivot Comparison (Phase 4)\n\n")
        f.write("| Dark Cute (Hyper-pop / Yami-Kawaii) | Neo-Anthemic (Heroic / Open) |\n")
        f.write("| --- | --- |\n")
        
        # Interleave lines for visual comparison
        dark_lines = results["dark_cute_breakdown"].splitlines()
        anthem_lines = results["anthemic_cinematic"].splitlines()
        
        max_lines = max(len(dark_lines), len(anthem_lines))
        for i in range(max_lines):
            d = dark_lines[i] if i < len(dark_lines) else ""
            a = anthem_lines[i] if i < len(anthem_lines) else ""
            # Escape pipes for markdown table
            f.write(f"| {d.replace('|', '/')} | {a.replace('|', '/')} |\n")

    print(f"\nComparison report generated: {report_path}")

if __name__ == "__main__":
    compare_stylistic_pivots()
