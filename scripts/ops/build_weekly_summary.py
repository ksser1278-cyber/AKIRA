# scripts/ops/build_weekly_summary.py
"""Day 10 — Ops Weekly Summary Generator.

Produces both JSON and Markdown reports covering the 10 required metrics:
1. Average imagery coverage
2. Average originality score
3. Artist imitation risk average
4. Nearest-neighbor similarity distribution
5. Canon admission rate
6. Cluster distribution
7. Hook grammar distribution
8. Hard fail / retry ratio
9. Hold ratio
10. Promotion grade distribution
"""

from __future__ import annotations

import json
import sys
import io
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    entries = []
    if not path.exists():
        return entries
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except: continue
    return entries


def _load_canon_tracks(canon_dir: Path) -> List[Dict[str, Any]]:
    tracks = []
    for p in canon_dir.glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                tracks.append(json.load(f))
        except: continue
    return tracks


def _safe_mean(values: List[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _distribution(values: List[str]) -> Dict[str, int]:
    return dict(Counter(values))


def build_summary(project_root: Path = PROJECT_ROOT) -> Dict[str, Any]:
    """Build the weekly ops summary from all available data."""
    
    # Sources
    admission_log = _load_jsonl(project_root / "outputs" / "admission_log.jsonl")
    canon_tracks = _load_canon_tracks(project_root / "data" / "canon_tracks")
    novelty_path = project_root / "data" / "novelty" / "novelty_index_v1.json"
    
    # Novelty profiles
    novelty_profiles = []
    if novelty_path.exists():
        with open(novelty_path, "r", encoding="utf-8") as f:
            novelty_profiles = json.load(f).get("profiles", [])
    
    # 1. Imagery Coverage (from admission log or critic data)
    imagery_scores = [e.get("imagery_coverage", 0.0) for e in admission_log if "imagery_coverage" in e]
    
    # 2. Originality Scores
    originality_scores = [e.get("originality", 0.0) for e in admission_log]
    
    # 3. Imitation Risk
    imitation_risks = [p.get("artist_imitation_risk", 0.0) for p in novelty_profiles]
    
    # 4. Nearest-neighbor similarity distribution
    nn_sims = [p.get("external_similarity", 0.0) for p in novelty_profiles]
    nn_buckets = {"< 0.1": 0, "0.1-0.2": 0, "0.2-0.3": 0, "0.3+": 0}
    for s in nn_sims:
        if s < 0.1: nn_buckets["< 0.1"] += 1
        elif s < 0.2: nn_buckets["0.1-0.2"] += 1
        elif s < 0.3: nn_buckets["0.2-0.3"] += 1
        else: nn_buckets["0.3+"] += 1
    
    # 5. Canon admission rate
    total_evals = len(admission_log)
    admitted = sum(1 for e in admission_log if e.get("status") in ("pass", "warn"))
    admission_rate = round(admitted / max(1, total_evals), 4)
    
    # 6. Cluster distribution (from canon)
    cluster_dist = _distribution([
        t.get("admission_info", {}).get("metrics", {}).get("cluster_id", "unknown")
        for t in canon_tracks
    ])
    
    # 7. Hook grammar distribution (from canon)
    hook_dist = defaultdict(int)
    for t in canon_tracks:
        hooks = t.get("admission_info", {}).get("metrics", {}).get("hooks", [])
        for h in hooks:
            hook_dist[h] += 1
    
    # 8+9. Hard fail / retry / hold ratios
    status_counts = Counter(e.get("status", "unknown") for e in admission_log)
    hard_fail = status_counts.get("reject", 0)
    hold = status_counts.get("hold", 0)
    
    # 10. Promotion grade distribution
    grade_dist = _distribution([p.get("composite_score", 0.0) > 80 and "elite" or "standard" for p in novelty_profiles])
    
    summary = {
        "report_timestamp": datetime.now(timezone.utc).isoformat(),
        "period": "weekly",
        "metrics": {
            "1_imagery_coverage_avg": _safe_mean(imagery_scores),
            "2_originality_score_avg": _safe_mean(originality_scores),
            "3_imitation_risk_avg": _safe_mean(imitation_risks),
            "4_nn_similarity_distribution": nn_buckets,
            "5_canon_admission_rate": admission_rate,
            "6_cluster_distribution": cluster_dist,
            "7_hook_grammar_distribution": dict(hook_dist),
            "8_hard_fail_count": hard_fail,
            "9_hold_count": hold,
            "10_grade_distribution": grade_dist,
        },
        "totals": {
            "total_evaluations": total_evals,
            "total_admitted": admitted,
            "total_canon_size": len(canon_tracks),
            "total_novelty_profiles": len(novelty_profiles)
        }
    }
    
    return summary


def save_summary(summary: Dict[str, Any], project_root: Path = PROJECT_ROOT):
    """Save summary as JSON and Markdown."""
    reports_dir = project_root / "reports" / "ops"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # JSON
    json_path = reports_dir / "weekly_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    # Markdown
    md_path = reports_dir / "weekly_summary.md"
    metrics = summary["metrics"]
    totals = summary["totals"]
    
    md_lines = [
        f"# AKIRA ENGINE — Weekly Ops Report",
        f"**Generated**: {summary['report_timestamp']}",
        "",
        "## Key Metrics",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Imagery Coverage (avg) | {metrics['1_imagery_coverage_avg']} |",
        f"| Originality Score (avg) | {metrics['2_originality_score_avg']} |",
        f"| Imitation Risk (avg) | {metrics['3_imitation_risk_avg']} |",
        f"| Canon Admission Rate | {metrics['5_canon_admission_rate']:.1%} |",
        f"| Hard Fails | {metrics['8_hard_fail_count']} |",
        f"| Holds | {metrics['9_hold_count']} |",
        "",
        "## Nearest-Neighbor Similarity Distribution",
        "",
        f"| Range | Count |",
        f"|-------|-------|",
    ]
    for bucket, count in metrics["4_nn_similarity_distribution"].items():
        md_lines.append(f"| {bucket} | {count} |")
    
    md_lines.extend([
        "",
        "## Cluster Distribution",
        "",
        f"| Cluster | Count |",
        f"|---------|-------|",
    ])
    for cluster, count in metrics["6_cluster_distribution"].items():
        md_lines.append(f"| {cluster} | {count} |")
    
    md_lines.extend([
        "",
        "## Totals",
        "",
        f"- Evaluations: {totals['total_evaluations']}",
        f"- Admitted: {totals['total_admitted']}",
        f"- Canon Size: {totals['total_canon_size']}",
        f"- Novelty Profiles: {totals['total_novelty_profiles']}",
    ])
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    
    print(f"[OPS] JSON report: {json_path}")
    print(f"[OPS] Markdown report: {md_path}")


if __name__ == "__main__":
    summary = build_summary()
    save_summary(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
