"""
normalize_conditioning_audits.py
================================
6개 프로듀서의 conditioning_audit_active.json에
top-level 집계 필드 (record_count, average_score, gold_count, usable_count, weak_count)를
records 배열에서 자동 계산하여 추가합니다.

이미 집계 필드가 있는 파일은 건너뜁니다.

NOTE: scores가 0~1 범위인 파일은 0~100으로 변환합니다 (pinocchiop/deco27 호환).
"""
from __future__ import annotations

import json
from pathlib import Path

AUDIT_DIR = (
    Path(__file__).resolve().parents[2]
    / "_quarantine"
    / "2026-04-03"
    / "archive"
    / "reports"
    / "quality"
    / "conditioning"
)

TARGET_ARTISTS = ["maretu", "kanaria", "kairiki_bear", "iyowa", "syudou", "neru"]


def normalize_audit(path: Path) -> bool:
    """Returns True if file was modified."""
    data = json.loads(path.read_text(encoding="utf-8"))

    # already normalized?
    if "record_count" in data and "average_score" in data:
        print(f"  SKIP {path.name} - already has aggregate fields")
        return False

    records = data.get("records", [])
    if not records:
        print(f"  SKIP {path.name} - no records")
        return False

    # normalize scores: 0~1 → 0~100
    for rec in records:
        score = float(rec.get("score", 0))
        if score <= 1.0:
            rec["score"] = round(score * 100, 1)

    scores = [float(rec.get("score", 0)) for rec in records]
    grades = [str(rec.get("grade", "")).lower() for rec in records]

    data["record_count"] = len(records)
    data["gold_count"] = grades.count("gold")
    data["usable_count"] = grades.count("usable")
    data["weak_count"] = grades.count("weak")
    data["average_score"] = round(sum(scores) / len(scores), 1) if scores else 0.0

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  DONE {path.name} - record_count={data['record_count']}, avg={data['average_score']}, gold={data['gold_count']}")
    return True


def main():
    print(f"Audit dir: {AUDIT_DIR}")
    modified = 0
    for artist_id in TARGET_ARTISTS:
        audit_path = AUDIT_DIR / f"{artist_id}_conditioning_audit_active.json"
        if not audit_path.exists():
            print(f"  MISS {artist_id} - file not found")
            continue
        if normalize_audit(audit_path):
            modified += 1

    print(f"\nNormalized {modified}/{len(TARGET_ARTISTS)} audit files.")


if __name__ == "__main__":
    main()
