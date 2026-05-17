from __future__ import annotations

from pathlib import Path
import pytest

from src.akira_engine.gpt_ab_experiment import ABExperimentConfig, compare_outputs, run_gpt_ab_experiment


DIRECT_OUTPUT = """# Direct
[Style Prompt]
vocaloid pop

[Lyrics]
[Intro]
hello
[Verse 1]
I chase the dream tonight
[Chorus]
heart heart
night light

[Self Check]
ok
"""


ASSISTED_OUTPUT = """# Assisted
[Style Prompt]
high-contrast vocaloid rock pop, synthetic lead vocal, tight consonants

[Lyrics]
[Intro]
ぱち ぱち
[Verse 1]
錆びた通知を ひとつ飲んだ
名前のない熱だけ 残った
[Pre-Chorus]
言えない でも消せない
秒針だけが先に泣く
[Chorus]
ぱちぱち バグって
またまた 光って
きみの嘘まで 歌にして
ぱちぱち バグって
まだまだ 欲しがって
[Bridge]
かわいいだけじゃ こわれない
[Final Chorus]
ぱちぱち バグって
またまた 光って

[Self Check]
AKIRA constraints used selectively.
"""


def test_run_gpt_ab_experiment_prompt_only(tmp_path: Path) -> None:
    manifest = run_gpt_ab_experiment(
        ABExperimentConfig(
            project_root=tmp_path,
            output_dir=tmp_path / "ab",
            intent="test intent",
            style="vocaloid subculture pop",
        )
    )

    assert manifest["execution_status"] == "prompt_only"
    assert Path(manifest["output_paths"]["direct_prompt"]).exists()
    assert "assisted_prompt" not in manifest["output_paths"]


def test_run_gpt_ab_experiment_requires_analysis_for_assisted_compare(tmp_path: Path) -> None:
    direct_path = tmp_path / "direct.md"
    assisted_path = tmp_path / "assisted.md"
    direct_path.write_text(DIRECT_OUTPUT, encoding="utf-8")
    assisted_path.write_text(ASSISTED_OUTPUT, encoding="utf-8")

    with pytest.raises(ValueError, match="requires --analysis-dir"):
        run_gpt_ab_experiment(
            ABExperimentConfig(
                project_root=tmp_path,
                output_dir=tmp_path / "ab",
                intent="test intent",
                style="vocaloid subculture pop",
                direct_output_path=direct_path,
                assisted_output_path=assisted_path,
            )
        )


def test_run_gpt_ab_experiment_compares_external_outputs_with_analysis(tmp_path: Path) -> None:
    direct_path = tmp_path / "direct.md"
    assisted_path = tmp_path / "assisted.md"
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir()
    direct_path.write_text(DIRECT_OUTPUT, encoding="utf-8")
    assisted_path.write_text(ASSISTED_OUTPUT, encoding="utf-8")
    (analysis_dir / "ai_reconstruction.json").write_text(
        """{
  "ai_reconstruction_profile": {
    "song_identity": {"surface": ["cute"], "inner": ["unstable"]},
    "core_intent": {"main_goal": "test"},
    "lyric_engine": {"line_style": "short"},
    "hook_engine": {"main_hook": "contrast"}
  }
}
""",
        encoding="utf-8",
    )
    (analysis_dir / "pass_5_recipe.json").write_text(
        """{"reuse_strategy": {"must_keep": ["contrast"], "can_change": ["image"], "avoid": ["generic"]}}""",
        encoding="utf-8",
    )

    manifest = run_gpt_ab_experiment(
        ABExperimentConfig(
            project_root=tmp_path,
            output_dir=tmp_path / "ab",
            intent="test intent",
            style="vocaloid subculture pop",
            analysis_dir=analysis_dir,
            direct_output_path=direct_path,
            assisted_output_path=assisted_path,
        )
    )

    assert manifest["execution_status"] == "external_outputs_compared"
    assert manifest["analysis_data_fields_present"] >= 2
    assisted_prompt = Path(manifest["output_paths"]["assisted_prompt"]).read_text(encoding="utf-8")
    assert "AKIRA collected-analysis data:" in assisted_prompt
    assert "Build a clear character rule" not in assisted_prompt


def test_compare_outputs_returns_delta() -> None:
    comparison = compare_outputs(DIRECT_OUTPUT, ASSISTED_OUTPUT)

    assert comparison["assisted_minus_direct"] > 0
