"""Smoke Test: Week 1 - Novelty Index.

Validates the corpus_intelligence.novelty module by:
1. Computing novelty profiles for sample generated lyrics
2. Building a novelty index from the existing corpus
3. Printing summary statistics
"""

from __future__ import annotations

import io
import sys
import time
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # scripts/ -> AKIRA ENGINE
sys.path.insert(0, str(PROJECT_ROOT))

from src.akira_engine.corpus_intelligence.novelty.schema import NoveltyProfile
from src.akira_engine.corpus_intelligence.novelty.similarity import (
    compute_text_similarity, compute_atom_jaccard, find_nearest_neighbor,
)
from src.akira_engine.corpus_intelligence.novelty.risk import (
    score_artist_imitation_risk, score_cliche_density, score_recombinative_novelty,
)
from src.akira_engine.corpus_intelligence.novelty.mod import (
    compute_novelty_profile, build_novelty_index, _load_external_corpus,
)
from src.akira_engine.features.mod import extract_atoms


def _separator(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_schema():
    """Test: NoveltyProfile can be instantiated and scored."""
    _separator("Test 1: Schema & Composite Scoring")

    p = NoveltyProfile(
        track_id="test_001",
        external_similarity=0.3,
        internal_similarity=0.1,
        artist_imitation_risk=0.2,
        cliche_density=0.15,
        recombinative_novelty=0.6,
        status="scored",
    )
    print(f"  track_id: {p.track_id}")
    print(f"  composite_score: {p.composite_score():.2f}")
    print(f"  to_dict keys: {list(p.to_dict().keys())}")
    assert p.composite_score() > 0.0, "Composite score should be positive"
    assert p.status == "scored"
    print("  ✓ PASSED")


def test_similarity():
    """Test: Text similarity and atom Jaccard."""
    _separator("Test 2: Similarity Functions")

    text_a = "壊れた窓の向こう側\n蛍光灯が瞬いて\n喉が焼ける夜明け前\n体温だけが残ってた"
    text_b = "壊れた窓の向こう側\n月明かりが差し込んで\n指先が震える夜明け前\n体温だけが消えていた"
    text_c = "桜の花びらが舞い散る\n春風に乗せた手紙\n約束の場所で待ってる\n君の笑顔が見たくて"

    sim_ab = compute_text_similarity(text_a, text_b)
    sim_ac = compute_text_similarity(text_a, text_c)
    print(f"  Similar pair (A↔B): {sim_ab:.4f}")
    print(f"  Different pair (A↔C): {sim_ac:.4f}")
    assert sim_ab > sim_ac, "Similar texts should have higher similarity"
    print("  ✓ PASSED")

    atoms_a = extract_atoms(text_a)
    atoms_b = extract_atoms(text_b)
    atoms_c = extract_atoms(text_c)
    jac_ab = compute_atom_jaccard(atoms_a, atoms_b)
    jac_ac = compute_atom_jaccard(atoms_a, atoms_c)
    print(f"  Atom Jaccard (A↔B): {jac_ab:.4f}")
    print(f"  Atom Jaccard (A↔C): {jac_ac:.4f}")
    assert jac_ab >= jac_ac, "Similar texts should have higher atom overlap"
    print("  ✓ PASSED")


def test_cliche_density():
    """Test: Cliché detection."""
    _separator("Test 3: Cliché Density")

    clean_text = "蛍光灯の隙間から\n指先に絡む静電気\n喉の奥が焼けるように\n体温の名残だけが残る"
    cliche_text = "永遠に君がいない\n涙が消えたい夢の中\n約束した世界の果て\n二人だけの時が止まる"

    clean_score = score_cliche_density(clean_text)
    cliche_score = score_cliche_density(cliche_text)
    print(f"  Clean text cliché density: {clean_score:.4f}")
    print(f"  Cliché-heavy text density:  {cliche_score:.4f}")
    assert cliche_score > clean_score, "Cliché text should score higher"
    print("  ✓ PASSED")


def test_recombinative_novelty():
    """Test: Recombinative novelty scoring."""
    _separator("Test 4: Recombinative Novelty")

    # Mixed sensory atoms (body + scene + sound + motif)
    mixed_atoms = ["喉", "体温", "蛍光", "窓", "ノイズ", "残響", "痛み", "叫び"]
    # Single category atoms (body only)
    single_atoms = ["喉", "指先", "瞳", "体温", "鼓動", "息", "肌"]

    mixed_score = score_recombinative_novelty(mixed_atoms)
    single_score = score_recombinative_novelty(single_atoms)
    print(f"  Mixed-category atoms:  {mixed_score:.2f}")
    print(f"  Single-category atoms: {single_score:.2f}")
    assert mixed_score > single_score, "Mixed categories should score higher"
    print("  ✓ PASSED")


def test_corpus_loading():
    """Test: External corpus loads correctly."""
    _separator("Test 5: Corpus Loading")

    corpus = _load_external_corpus(PROJECT_ROOT)
    print(f"  External corpus entries: {len(corpus)}")

    if corpus:
        sample = corpus[0]
        print(f"  Sample track_id: {sample['track_id']}")
        print(f"  Sample artist_id: {sample['artist_id']}")
        print(f"  Sample text length: {len(sample['text'])}")
        print(f"  Sample atom count: {len(sample['atoms'])}")
        print("  ✓ PASSED (corpus loaded)")
    else:
        print("  ⚠ No conditioning files found — corpus is empty")
        print("  ✓ PASSED (graceful empty handling)")


def test_novelty_profile():
    """Test: Full novelty profile computation."""
    _separator("Test 6: Full Novelty Profile")

    candidate = (
        "[Verse 1]\n"
        "蛍光灯の隙間から差し込む光\n"
        "指先に絡む静電気みたいに\n"
        "喉の奥が焼けるようなこの感覚\n"
        "体温の名残だけが残っている\n\n"
        "[Chorus]\n"
        "壊れた窓の向こう側で\n"
        "叫びが反響して消えていく\n"
        "痛みだけが本物だと\n"
        "知ってしまった夜\n"
    )

    t0 = time.time()
    profile = compute_novelty_profile(
        candidate_text=candidate,
        track_id="smoke_test_001",
        target_artist_id="maretu",
        project_root=PROJECT_ROOT,
        top_k=3,
    )
    elapsed = time.time() - t0

    print(f"  Track ID: {profile.track_id}")
    print(f"  External similarity: {profile.external_similarity:.4f}")
    print(f"  Internal similarity: {profile.internal_similarity:.4f}")
    print(f"  Artist imitation risk: {profile.artist_imitation_risk:.4f}")
    print(f"  Cliché density: {profile.cliche_density:.4f}")
    print(f"  Recombinative novelty: {profile.recombinative_novelty:.4f}")
    print(f"  Composite score: {profile.composite_score():.2f}")
    print(f"  Status: {profile.status}")
    print(f"  Nearest external: {profile.nearest_external_track.track_id} ({profile.nearest_external_track.similarity:.4f})")
    print(f"  Top-k external count: {len(profile.top_k_external)}")
    print(f"  Elapsed: {elapsed:.2f}s")
    assert profile.status == "scored"
    assert profile.composite_score() >= 0.0
    print("  ✓ PASSED")


def test_novelty_index_build():
    """Test: Build novelty index."""
    _separator("Test 7: Novelty Index Build")

    output_path = PROJECT_ROOT / "data" / "novelty" / "novelty_index_v1.json"

    t0 = time.time()
    index = build_novelty_index(
        project_root=PROJECT_ROOT,
        output_path=output_path,
    )
    elapsed = time.time() - t0

    print(f"  Corpus size: {index['corpus_size']}")
    print(f"  Canon size: {index['canon_size']}")
    print(f"  Profiles computed: {len(index['profiles'])}")
    print(f"  Output: {output_path}")
    print(f"  Elapsed: {elapsed:.2f}s")

    if "statistics" in index:
        stats = index["statistics"]
        for key, stat in stats.items():
            print(f"  {key}: mean={stat['mean']:.4f}, min={stat['min']:.4f}, max={stat['max']:.4f}")

    assert output_path.exists(), "Index file should be created"
    print("  ✓ PASSED")


if __name__ == "__main__":
    print("===========================================================")
    print("  AKIRA ENGINE - Week 1 Smoke Test: Novelty Index")
    print("===========================================================")

    tests = [
        test_schema,
        test_similarity,
        test_cliche_density,
        test_recombinative_novelty,
        test_corpus_loading,
        test_novelty_profile,
        test_novelty_index_build,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1

    _separator("Summary")
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")

    if failed > 0:
        sys.exit(1)
    else:
        print("\n  All tests passed! ✓")
        sys.exit(0)
