import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from akira_engine.synthesizer import LyricSynthesizer
from akira_engine.gemini_songwriter import run_gemini_request_bundle

def run_audit_synthesis():
    project_root = Path(__file__).parent
    brief_dir = project_root / "outputs/audit/briefs"
    output_bundle = project_root / "outputs/audit/requests.jsonl"
    
    synthesizer = LyricSynthesizer(project_root)
    records = []

    # PinocchioP
    pp_profile = json.loads((project_root / "artists/pinocchiop/profile.json").read_text(encoding="utf-8"))
    for i in range(1, 4):
        brief_path = brief_dir / f"audit_pp_{i:02}.md"
        if brief_path.exists():
            brief_content = brief_path.read_text(encoding="utf-8")
            record = synthesizer.prepare_request_record("pinocchiop", f"audit_pp_{i:02}", brief_content, pp_profile)
            records.append(record)

    # DECO*27
    deco_profile = json.loads((project_root / "artists/deco27/profile.json").read_text(encoding="utf-8"))
    for i in range(1, 4):
        brief_path = brief_dir / f"audit_deco_{i:02}.md"
        if brief_path.exists():
            brief_content = brief_path.read_text(encoding="utf-8")
            record = synthesizer.prepare_request_record("deco27", f"audit_deco_{i:02}", brief_content, deco_profile)
            records.append(record)

    # Write request bundle
    output_bundle.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records), encoding="utf-8")
    print(f"Created request bundle at {output_bundle}")

    # Run synthesis
    print("Starting synthesis...")
    output_results = project_root / "outputs/audit/results"
    output_results.mkdir(parents=True, exist_ok=True)
    
    run_gemini_request_bundle(
        requests_jsonl=output_bundle,
        project_root=project_root,
        output_dir=output_results,
        model="gemini-3-flash-preview", # Use the same model as production
        api_url="https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds=60,
        temperature=1.0,
        top_p=0.95,
        max_output_tokens=8192, # Increased to accommodate thinking tokens
        thinking_level=None,
        retry_attempts=3,
        sleep_seconds=2.0
    )

if __name__ == "__main__":
    run_audit_synthesis()
