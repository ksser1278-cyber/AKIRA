"""Integration Test: Week 3 - Motif Transition Graph on Real Corpus.

Builds the graph from the 100 tracks in the existing corpus and
prints out some interesting statistics (top transitions, top motifs, etc.)
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

from src.akira_engine.corpus_intelligence.motifs.mod import build_motif_graph_index
from src.akira_engine.corpus_intelligence.novelty.mod import _load_external_corpus

def run_integration_test():
    print("===========================================================")
    print("  AKIRA ENGINE - Week 3 Integration: Real Corpus Graph")
    print("===========================================================")

    # 1. Load real corpus records
    print(f"Loading corpus from: {PROJECT_ROOT}")
    # Note: _load_external_corpus returns list of dicts with text/atoms/track_id/artist_id
    # But those are processed versions. We need the raw conditioning records for section_analysis.
    
    # Let's find all *.conditioning.json files manually for full fidelity
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

    # 2. Build graph index
    output_path = PROJECT_ROOT / "data" / "motifs" / "motif_transition_graph_v1.json"
    result = build_motif_graph_index(
        records,
        output_path=output_path,
        min_support_count=2
    )

    print(f"\nBuild Results:")
    print(f" - Output: {result['output_path']}")
    print(f" - Nodes (Motifs): {result['node_count']}")
    print(f" - Edges (Transitions): {result['edge_count']}")

    # 3. Analyze Graph
    with open(output_path, "r", encoding="utf-8") as f:
        graph_data = json.load(f)

    # Top Motifs
    stats = graph_data.get("motif_stats", {})
    top_motifs = sorted(stats.values(), key=lambda x: x['frequency'], reverse=True)[:10]
    print("\nTop 10 Motifs by Frequency:")
    for m in top_motifs:
        print(f" - {m['motif']}: {m['frequency']} (In: {m['incoming_count']}, Out: {m['outgoing_count']})")

    # Top Transitions
    all_transitions = []
    for src, targets in graph_data.get("transitions", {}).items():
        for t in targets:
            all_transitions.append(t)
    
    top_trans = sorted(all_transitions, key=lambda x: x['weight'], reverse=True)[:10]
    print("\nTop 10 Transitions by Weight:")
    for t in top_trans:
        print(f" - {t['src_motif']} -> {t['dst_motif']} [{t['transition_type']}] weight={t['weight']:.2f} (support={t['support_count']})")

    # Sample a chain
    from src.akira_engine.corpus_intelligence.motifs.graph import sample_transition_chain, score_transition_novelty, MotifGraph, MotifTransition

    # Reconstruct graph for sampling test
    transitions = {k: [MotifTransition(**item) for item in v] for k, v in graph_data.get("transitions", {}).items()}
    graph_obj = MotifGraph(
        version=graph_data['version'],
        node_count=graph_data['node_count'],
        edge_count=graph_data['edge_count'],
        transitions=transitions,
        motif_stats={},
        sampling_index=graph_data['sampling_index']
    )

    if top_motifs:
        start_motif = top_motifs[0]['motif']
        print(f"\nSampling Chain starting from '{start_motif}':")
        chain = sample_transition_chain(graph_obj, start_motif=start_motif, max_steps=4)
        for i, step in enumerate(chain):
            print(f" Step {i+1}: {step['src_motif']} --({step['transition_type']})--> {step['dst_motif']}")
        
        novelty = score_transition_novelty(graph_obj, chain)
        print(f"Chain Novelty Score: {novelty:.4f}")

    print("\nIntegration test complete!")

if __name__ == "__main__":
    run_integration_test()
