import sys
import os
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.akira_engine.gemini_songwriter import load_api_key, DEFAULT_API_URL, DEFAULT_MODEL, response_text

def run_maretu_somatic():
    project_root = Path(__file__).resolve().parents[2]
    api_key = load_api_key(project_root)
    
    system_prompt = (
        "You are the internal 'Hyper-Fidelity' songwriting unit of AKIRA ENGINE, specialized in the artist MARETU.\n"
        "Your objective: Generate a 100% original MARETU masterpiece that captures his *true* somatic and clinical essence.\n\n"
        "MARETU STYLE CONSTRAINTS (MANDATORY):\n"
        "1. WEAPON_KEIGO_CRUELTY: Use extremely formal/polite Japanese (です/ます/ございます) to describe visceral, disgusting, or surgically painful acts. The tone should be clinical and detached.\n"
        "2. WEAPON_SOMATIC_PRECISION: Avoid generic 'pain.' Use terms like '内臓' (viscera), '脳漿' (cerebrospinal fluid), '粘膜' (mucus membrane), '網膜' (retina), '膿' (pus), '歯車' (gears), '腐敗' (decay).\n"
        "3. WEAPON_RHYTHMIC_PHRASING: Use repetitive 5-7-5 or 4-4 word clusters, often triplet verbs (e.g., '見つめて 繋げて 射止めて').\n"
        "4. WEAPON_PHONETIC_GLITCH: Use rhythmic stutters like 'は・は・は・這いずって' or 'き・き・き・気持ち悪い.'\n"
        "5. SONIC_CUE: Include an English 'Slogan' at the start (e.g., 'WELCOME TO THE MIND FUCK').\n\n"
        "THEME: 'Somatic Rejection of a Parasitic Love.' Describe emotional obsession as a physical tumor that needs clinical extraction.\n"
        "BAN_LIST: 'Update failed', 'Mayday', 'Vampire', 'Ghost', 'Trash', 'Noble', 'Bite me'. Avoid clean 'digital' metaphors; lean into 'dirty/medical' ones.\n\n"
        "Return MARKDOWN formatting only.\n"
        "1. Suno [Style] block at the top ([Style: Brutal Chiptune Metal, Heavy Bass, Glitchy, Polite Cruelty]).\n"
        "2. # <Japanese Title>\n"
        "3. Section headers: [Intro], [Verse 1], [Pre-Chorus], [Chorus], [Bridge], [Final Chorus], [Outro]."
    )
    
    user_prompt = (
        "Write a MARETU masterpiece titled '膿(うみ)と執着(しゅうちゃく)' (Pus and Obsession). \n"
        "Vibe: An obsessive, one-sided devotion that has physically rotted the narrator's organs. The 'love' is now a disease that must be surgically removed while remaining perfectly polite to the subject."
    )
    
    url = f"{DEFAULT_API_URL}/models/{DEFAULT_MODEL}:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 1.0, "topP": 0.99, "maxOutputTokens": 3072},
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    print("Generating MARETU Somatic Masterpiece...")
    res = requests.post(url, headers=headers, json=body, timeout=120)
    if res.status_code != 200:
        print(f"Error: {res.status_code} - {res.text}")
        sys.exit(1)
        
    text = response_text(res.json())
    
    out_dir = project_root / "outputs" / "demo" / "maretu_somatic_demo"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "masterpiece_lyric.md"
    out_file.write_text(text, encoding="utf-8")
    print(f"Success! Masterpiece lyrics written to {out_file}")

if __name__ == "__main__":
    run_maretu_somatic()
