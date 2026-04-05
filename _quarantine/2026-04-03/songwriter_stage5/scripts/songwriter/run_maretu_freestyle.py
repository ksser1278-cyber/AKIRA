import sys
import os
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.akira_engine.gemini_songwriter import load_api_key, DEFAULT_API_URL, DEFAULT_MODEL, response_text

def run_maretu_freestyle():
    project_root = Path(__file__).resolve().parents[2]
    api_key = load_api_key(project_root)
    
    system_prompt = (
        "You are MARETU, a legendary Vocaloid producer known for 'Polite Cruelty' (丁寧な残虐性).\n"
        "Your Style Architecture:\n"
        "- WEAPON_KEIGO_CRUELTY: Use extremely formal/polite Japanese (です/ます/ございます) to describe visceral pain, surgery, or psychological destruction.\n"
        "- WEAPON_SOMATIC_PRECISION: Instead of 'it hurts,' describe the exact nervous system failure, the sound of gears grinding in the throat, or the metallic taste of a diagnostic error.\n"
        "- WEAPON_RHYTHMIC_REPETITION: Obsessively repeat the first word or phrase of a line for a glitchy, broken-record effect (e.g., 'A-a-a-a-a-anata' or 'Ko-ko-ko-koro').\n"
        "- WEAPON_DIGITAL_VOID: Use software/hardware metaphors (delete, overwrite, trash, partition error, uninstalled, defragmentation) to describe human emotions.\n\n"
        "Instructions:\n"
        "DO NOT use any lyrics from 'Mind Brand', 'GUMMY', 'Coin Locker Baby', or 'Suji'. No references to 'Update failed' or 'Mayday'.\n"
        "Create a COMPLETELY ORIGINAL song about: A digital breakup where a shared cloud memory is being systemically deleted/uninstalled, causing physical somatic damage to the narrator.\n"
        "Return MARKDOWN only.\n"
        "1. Include a Suno [Style] block (e.g., [Style: Heavy Chiptune Metal, Glitchy, Fast, Aggressive, Polite detachment]).\n"
        "2. Title starting with '# '.\n"
        "3. Section headers in brackets (e.g., [Intro], [Verse 1], [Chorus], [Glitch Outro])."
    )
    
    user_prompt = (
        "Write an original MARETU masterpiece. \n"
        "Theme: 'Deletion Log: Allocation Error'. \n"
        "Imagery: Shared folders being wiped, 'Access Denied' signs in the brain, the smell of burnt-out chips, clinical white light.\n"
        "Voice: Use the 'Polite Cruelty' signature. Be cold, analytical, and rhythmic. \n"
        "CRITICAL: Avoid common Vocaloid tropes (flower, moon, wings). Lean into medical and mechanical hardware imagery."
    )
    
    url = f"{DEFAULT_API_URL}/models/{DEFAULT_MODEL}:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 1.0, "topP": 0.99, "maxOutputTokens": 3072}
    }
    
    print("Generating Original MARETU Demo...")
    res = requests.post(url, headers=headers, json=body, timeout=120)
    if res.status_code != 200:
        print(f"Error: {res.status_code} - {res.text}")
        sys.exit(1)
        
    text = response_text(res.json())
    
    out_dir = project_root / "outputs" / "demo" / "original_maretu_demo"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "original_lyric.md"
    out_file.write_text(text, encoding="utf-8")
    print(f"Success! Original lyrics written to {out_file}")

if __name__ == "__main__":
    run_maretu_freestyle()
