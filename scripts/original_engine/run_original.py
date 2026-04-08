"""
run_original.py
===============
AKIRA Original Lyric Engine — CLI 진입점

Usage:
    python scripts/original_engine/run_original.py "자유형식 입력"
    python scripts/original_engine/run_original.py "새벽 3시, 실연, 마지막은 폭발적으로"

Output:
    outputs/original/{session_id}/
        lyrics.md           ← 구조화된 가사 (마크다운)
        suno_prompt.json    ← Suno 완전 포맷
        quality_report.json ← 품질 채점 결과
        session.json        ← 세션 메타데이터
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

from akira_engine.original.direction_parser import parse_direction
from akira_engine.original.technique_sampler import sample_technique_context
from akira_engine.original.lyric_generator import generate_lyrics
from akira_engine.original.quality_scorer import score_lyrics
from akira_engine.original.suno_formatter import format_suno_prompt

LIB_ROOT = ROOT / "data" / "technique_library"
OUTPUT_ROOT = ROOT / "outputs" / "original"
API_KEY_PATH = ROOT.parent / "API KEY.txt"


def load_api_key() -> str:
    # 1. 환경변수
    for var in ("OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"):
        val = os.getenv(var)
        if val:
            print(f"      [DEBUG] Key loaded from ENV: {var}")
            return val.strip()
            
    # 2. config/.env
    env_path = (ROOT / "config" / ".env").resolve()
    if env_path.exists():
        try:
            # utf-8-sig handles UTF-8 with BOM
            text = env_path.read_text(encoding="utf-8-sig")
            for line in text.splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    k = k.strip()
                    if k in ("OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"):
                        print(f"      [DEBUG] Key loaded from .env: {k}")
                        return v.strip()
        except Exception as e:
            print(f"      [DEBUG] Error reading .env: {e}")
                    
    # 3. 상위 API KEY.txt
    if API_KEY_PATH.exists():
        val = API_KEY_PATH.read_text(encoding="utf-8").strip()
        print(f"      [DEBUG] Key loaded from API KEY.txt (fallback)")
        return val
        
    raise ValueError("API key not found.")


def make_session_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_outputs(
    session_id: str,
    raw_input: str,
    direction_dict: dict,
    lyrics_md: str,
    suno_dict: dict,
    quality_dict: dict,
) -> Path:
    out_dir = OUTPUT_ROOT / session_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # 가사 마크다운
    (out_dir / "lyrics.md").write_text(lyrics_md, encoding="utf-8")

    # Suno 프롬프트
    (out_dir / "suno_prompt.json").write_text(
        json.dumps(suno_dict, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 품질 보고서
    (out_dir / "quality_report.json").write_text(
        json.dumps(quality_dict, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 세션 메타데이터
    session_meta = {
        "session_id": session_id,
        "raw_input": raw_input,
        "created_at": datetime.now().isoformat(),
        "direction": direction_dict,
        "output_files": {
            "lyrics": str(out_dir / "lyrics.md"),
            "suno_prompt": str(out_dir / "suno_prompt.json"),
            "quality_report": str(out_dir / "quality_report.json"),
        },
    }
    (out_dir / "session.json").write_text(
        json.dumps(session_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return out_dir


def run(raw_input: str) -> int:
    print("=" * 60)
    print(" AKIRA ORIGINAL LYRIC ENGINE (DNA BANK V1.1) ")
    print("=" * 60)
    print(f"\n  Input: {raw_input}\n")

    api_key = load_api_key()
    session_id = make_session_id()

    # 인코딩 안전 출력 처리 함수
    def safe_print(text):
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode('ascii', 'replace').decode('ascii'))

    # -- Step 1: Direction Parsing ------------------------------
    print("- [1/4] Parsing Direction...")
    direction = parse_direction(raw_input, api_key=api_key)
    safe_print(f"      Tone:    {direction.emotional_tone}")
    safe_print(f"      Arc:     {direction.energy_arc}")
    safe_print(f"      Preset:  {direction.matched_preset or 'none'}")
    safe_print(f"      Themes:  {', '.join(direction.theme_keywords)}")

    # -- Step 2: Technique Sampling -----------------------------
    print("- [2/4] Sampling Technique DNA...")
    technique = sample_technique_context(direction, lib_root=LIB_ROOT)
    
    imagery_preview = ", ".join(technique.imagery_bank[:5])
    safe_print(f"      Imagery bank: {imagery_preview}...")
    safe_print(f"      Hook density: {technique.hook_pattern.get('hook_density', '?')}")
    print(f"      Sections:     {len(technique.section_structure)}")

    # -- Step 3: Lyric Generation -------------------------------
    print("- [3/4] Generating Lyrics (gpt-5.4)...")
    t0 = time.time()
    lyrics = generate_lyrics(direction, technique, api_key=api_key)
    elapsed = time.time() - t0

    if not lyrics.generation_ok:
        safe_print(f"  x Generation failed: {lyrics.error}")
        return 1

    print(f"      Generated in {elapsed:.1f}s")
    print("-" * 60)
    safe_print(f" TITLE: {lyrics.title_suggestion}")
    print("-" * 60)
    safe_print(f"      Sections: {list(lyrics.sections.keys())}")

    # -- Step 4: Quality Scoring --------------------------------
    print("- [4/4] Scoring Quality...")
    report = score_lyrics(lyrics, direction)
    print(f"      Composite score:      {report.composite_score:.1f}/100")
    print(f"      Imagery specificity:  {report.imagery_specificity:.2f}")
    print(f"      Singability:          {report.singability:.2f}")
    print(f"      Emotional coherence:  {report.emotional_coherence:.2f}")
    print(f"      Structural integrity: {report.structural_integrity:.2f}")
    print(f"      Japanese quality:     {report.japanese_quality:.2f}")
    if not report.passes_threshold:
        print(f"      ! Below threshold (72.0) - alerts:")
        for alert in report.to_dict().get("alerts", []):
            safe_print(f"        - {alert}")

    # -- Step 5: Suno Formatting --------------------------------
    print("\n[5/5] Formatting Suno prompt...")
    suno = format_suno_prompt(lyrics, direction, report)
    safe_print(f"      Style: {', '.join(suno.style_tags[:3])}...")
    print(f"      BPM:   {suno.bpm_range[0]}-{suno.bpm_range[1]}")

    # -- Save Outputs -------------------------------------------
    lyrics_md = suno.to_markdown()
    out_dir = save_outputs(
        session_id=session_id,
        raw_input=raw_input,
        direction_dict=direction.to_dict(),
        lyrics_md=lyrics_md,
        suno_dict=suno.to_dict(),
        quality_dict=report.to_dict(),
    )

    # -- Summary ------------------------------------------------
    print("\n" + "=" * 60)
    print(f"  v Complete — session: {session_id}")
    print(f"  Score: {report.composite_score:.1f}/100 "
          f"({'PASS' if report.passes_threshold else 'REVIEW NEEDED'})")
    safe_print(f"\n- Style: {suno.style_tags}")
    safe_print(f"    suno_prompt.json    <- Suno 프롬프트")
    safe_print(f"    quality_report.json <- 품질 보고서")
    print("=" * 60 + "\n")

    # 터미널에 가사 미리보기 출력
    print("-- Lyrics Preview -------------------------------------\n")
    for name, content in lyrics.section_list:
        safe_print(f"\n[{name}]")
        safe_print(content)
        print()
        print()

    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python run_original.py \"자유형식 입력\"")
        print("Example: python run_original.py \"새벽 3시, 실연, 마지막은 폭발적으로\"")
        return 1
    raw_input = " ".join(sys.argv[1:])
    return run(raw_input)


if __name__ == "__main__":
    sys.exit(main())
