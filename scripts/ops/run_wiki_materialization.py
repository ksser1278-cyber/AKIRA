import sys
from pathlib import Path

# Add src to sys.path to allow imports from akira_engine
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / "src"))

from akira_engine.akira_wiki_materializer import materialize_akira_wiki

def main():
    canonical_corpus_root = project_root / "datasets/_global/vocaloid_metadata_canonical/tier1_map_seed"
    generation_root = project_root / "datasets/training/generation_profiles/tier1_map_seed_pilot10_sound_reviewed_v3"
    readiness_manifest_path = project_root / "reports/planning/generation_readiness_audit/tier1_map_seed_pilot10_sound_reviewed_v3/generation_readiness_audit.json"
    output_root = project_root / "wiki"

    print(f"Materializing AKIRA Wiki...")
    manifest = materialize_akira_wiki(
        canonical_corpus_root=canonical_corpus_root,
        generation_root=generation_root,
        readiness_manifest_path=readiness_manifest_path,
        output_root=output_root
    )
    
    print(f"Materialization complete!")
    print(f"Track pages: {manifest['counts']['track_pages']}")
    print(f"Output: {manifest['outputs']['wiki_root']}")

if __name__ == "__main__":
    main()
