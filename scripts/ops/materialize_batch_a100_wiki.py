import sys
from pathlib import Path

# Add src to sys.path to allow imports from akira_engine
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / "src"))

from akira_engine.akira_wiki_materializer import materialize_akira_wiki

def main():
    # Adjusted for batch_a100
    canonical_corpus_root = project_root / "datasets/training/lyric_technique_acquisition_queue/batch_a100"
    # Mapping 'accepted' to where the grounded records are
    
    # We will use the normalized lyrics as 'generation' records for the wiki for now
    generation_root = project_root / "lyrics/normalized/batch_a100"
    # Actually, generation_root needs a 'records' subfolder according to the materializer
    
    readiness_manifest_path = project_root / "reports/planning/generation_readiness_audit/batch_a100/generation_readiness_audit.json"
    output_root = project_root / "wiki"

    print(f"Materializing AKIRA Wiki (Batch A100)...")
    manifest = materialize_akira_wiki(
        canonical_corpus_root=canonical_corpus_root,
        generation_root=project_root / "lyrics/normalized", # This might need a 'batch_a100' records folder
        readiness_manifest_path=readiness_manifest_path,
        output_root=output_root
    )
    
    print(f"Materialization complete!")
    print(f"Track pages: {manifest['counts']['track_pages']}")
    print(f"Output: {manifest['outputs']['wiki_root']}")

if __name__ == "__main__":
    main()
