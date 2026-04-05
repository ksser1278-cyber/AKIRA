from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.akira_engine.cli import run_songwriter_demo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run artist-synthesis demo songwriting from a composite demo plan.",
    )
    parser.add_argument("--artist-id", required=True, help="Artist id such as deco27 or pinocchiop.")
    parser.add_argument("--mode-id", help="Optional mode id. Defaults to the representative profile priority.")
    parser.add_argument("--intent", help="Optional high-level intent.")
    parser.add_argument("--title-seed", help="Optional title seed.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Project root. Defaults to the repository root.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs") / "demo_songwriter",
        help="Output directory root.",
    )
    parser.add_argument(
        "--candidate-count",
        type=int,
        default=4,
        help="Number of candidates to generate before critique.",
    )
    parser.add_argument(
        "--generation-mode",
        choices=["auto", "template", "llm"],
        default="auto",
        help="Generation backend policy. 'auto' falls back to template only when provider is unavailable.",
    )
    parser.add_argument(
        "--model-provider",
        choices=["gemini", "gpt", "openai"],
        default="gpt",
        help="LLM provider: 'gemini' (Google) or 'gpt'/'openai' (OpenAI).",
    )
    parser.add_argument(
        "--model-name",
        help="Override the default model name (e.g. gpt-4o, gemini-1.5-pro).",
    )
    return parser.parse_args()


def main() -> None:
    # Fix Unicode output on Windows terminals (CP949/CP932)
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    args = parse_args()
    manifest = run_songwriter_demo(
        project_root=args.project_root.resolve(),
        artist_id=args.artist_id,
        mode_id=args.mode_id,
        output_dir=args.output_dir,
        candidate_count=args.candidate_count,
        intent=args.intent or "",
        title_seed=args.title_seed or "",
        model_provider=args.model_provider,
        model_name=args.model_name,
        generation_mode=args.generation_mode,
    )

    print(f"Demo run manifest: {manifest['manifest_path']}")
    print(f"Selected lyric: {manifest['selected_lyric_path']}")
    print(f"Winning candidate: {manifest['selected_candidate_id']}")
    print(f"Winning score: {manifest['selected_score']}")
    print(f"Requested generation mode: {manifest.get('requested_generation_mode', 'auto')}")
    print(f"Resolved generation mode: {manifest.get('generation_mode', 'template')}")
    print(f"Source root: {manifest.get('source_root', args.project_root.resolve())}")


if __name__ == "__main__":
    main()
