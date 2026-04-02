import sys
import os
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.akira_engine.gemini_songwriter import load_api_key, DEFAULT_API_URL, DEFAULT_MODEL, response_text

def run_freestyle():
    project_root = Path(__file__).resolve().parents[2]
    api_key = load_api_key(project_root)
    
    system_prompt = (
        "You are a visionary Japanese songwriter crafting a high-fidelity Vocaloid/Pop-Punk track from scratch.\n"
        "Your Persona:\n"
        "DECO*27's architecture relies on juxtaposing high-energy, infectious pop-punk/rock instrumentation with intensely obsessive, needy, and slightly toxic lyrical themes. The core engine is \"performative vulnerability\"—using cute or catchy wrappers to deliver themes of painful dependency. Sentences should parse as fast, conversational direct address.\n\n"
        "Instructions:\n"
        "Do not follow any pre-existing structural plan or metric. Build a completely fresh, original song structure that naturally fits the user's intent. Do not just recycle the word '傷' (Kizu) or standard templates.\n"
        "Return MARKDOWN formatting only (no chat, no intro).\n"
        "1. Include a Suno [Style] block at the very top (e.g., [Style: Heavy Autotune, Vocaloid, Fast Pop Punk, aggressive rhythm]).\n"
        "2. The first line after style must be '# <Japanese Title>'.\n"
        "3. Section headers must be in brackets (e.g., [Verse 1], [Chorus]).\n"
        "4. Include meta-tags naturally for Suno (e.g., [Bass Drop], [Glitch Effect], [Heavy Compression])."
    )
    
    user_prompt = (
        "Write a complete Japanese song embodying the underlying *vibe* of a 'Cheeky Fallen Angel' (건방진 타락 천사) through a modern psychological toxic-romance metaphor. "
        "CRITICAL CONSTRAINT: DO NOT write a patchwork of famous DECO*27 tropes. "
        "BAN the following clichés: 'Update failed', 'Mayday', phrases ending in 'Vampire', 'Ghost', 'Trash', 'Noble', 'Bite me', or any direct pastiches of his existing hit songs. "
        "Instead, invent a COMPLETELY NEW, hyper-original vocabulary set and conceptual angle that DECO*27 has *never* used before, but apply his signature fast-paced rhythmic pacing, intense dependency, and conversational sass. "
        "The theme is: An arrogant romantic partner who willingly 'falls from grace' just to forcefully drag the listener down into their messy, obsessive world. "
        "Use visceral, unique metaphors (e.g., related to gambling, physics, unique modern subcultures, or unconventional chemistry) instead of standard internet-slang tropes. "
        "Start completely fresh and blow my mind!"
    )
    
    url = f"{DEFAULT_API_URL}/models/{DEFAULT_MODEL}:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.95, "topP": 0.99, "maxOutputTokens": 2048}
    }
    
    print("Calling Gemini API...")
    res = requests.post(url, headers=headers, json=body, timeout=120)
    if res.status_code != 200:
        print(f"Error: {res.status_code} - {res.text}")
        sys.exit(1)
        
    text = response_text(res.json())
    
    out_dir = project_root / "outputs" / "freestyle"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "freestyle_fallen_angel.md"
    out_file.write_text(text, encoding="utf-8")
    print(f"Success! Freestyle lyrics written to {out_file}")

if __name__ == "__main__":
    run_freestyle()
