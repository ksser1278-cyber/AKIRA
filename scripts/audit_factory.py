import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))
from akira_engine.generator import GenerationRequest, generate_package

def run_audit_batch():
    artist_base = Path("artists")
    output_base = Path("outputs/audit/briefs")
    output_base.mkdir(parents=True, exist_ok=True)

    test_cases = [
        # PinocchioP
        {
            "artist": "pinocchiop",
            "mode": "satirical_pop",
            "theme": "Artificial Intelligence",
            "emotion": "Sarcastic",
            "narrative": "AI tries to capture artist soul but fails due to its own template.",
            "id": "audit_pp_01"
        },
        {
            "artist": "pinocchiop",
            "mode": "experimental_chaos",
            "theme": "Social Media Toxicity",
            "emotion": "Urgent",
            "narrative": "A digital mask starts to crack under the weight of algorithm feeds.",
            "id": "audit_pp_02"
        },
        {
            "artist": "pinocchiop",
            "mode": "philosophical_nihilism",
            "theme": "Meaningless Existence",
            "emotion": "Detached",
            "narrative": "Finding peace in the emptiness of a convenience store at 3 AM.",
            "id": "audit_pp_03"
        },
        # DECO*27
        {
            "artist": "deco27",
            "mode": "electro_gloss",
            "theme": "Obsessive Love",
            "emotion": "Intense",
            "narrative": "A toxic circular attachment that feels like a rhythmic drug.",
            "id": "audit_deco_01"
        },
        {
            "artist": "deco27",
            "mode": "classic_rock_roots",
            "theme": "Self-Contradiction",
            "emotion": "Raw",
            "narrative": "Yelling a confession while knowing it's a lie.",
            "id": "audit_deco_02"
        },
        {
            "artist": "deco27",
            "mode": "denpa_chaos",
            "theme": "Digital Overload",
            "emotion": "Hyper",
            "narrative": "Sensory explosion in a neon-lit psychological basement.",
            "id": "audit_deco_03"
        }
    ]

    for case in test_cases:
        req = GenerationRequest(
            artist_file=artist_base / case["artist"] / "profile.json",
            mode_id=case["mode"],
            theme=case["theme"],
            emotion=case["emotion"],
            narrative=case["narrative"],
            output_path=output_base / f"{case['id']}.md"
        )
        print(f"Generating Brief: {case['id']}...")
        generate_package(req)

if __name__ == "__main__":
    run_audit_batch()
