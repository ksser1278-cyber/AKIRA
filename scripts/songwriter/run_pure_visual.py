import sys
import os
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.akira_engine.gemini_songwriter import load_api_key, DEFAULT_API_URL, DEFAULT_MODEL, response_text

def run_pure_visual_song():
    project_root = Path(__file__).resolve().parents[2]
    api_key = load_api_key(project_root)
    
    system_prompt = (
        "You are an artistic and atmospheric Japanese songwriter. Your goal is to write a song purely inspired by a specific visual aesthetic.\n"
        "Do not try to mimic any specific producer. Focus entirely on painting a beautiful, mesmerizing, and slightly dark auditory landscape.\n"
        "Return MARKDOWN formatting only (no conversational text).\n"
        "1. Include a Suno [Style] block at the top (suggest the best musical genre that fits the visual).\n"
        "2. The first line after style must be '# <Japanese Title>'.\n"
        "3. Section headers must be in brackets (e.g., [Verse 1], [Chorus]).\n"
        "4. Include musical meta-tags naturally (e.g., [Atmospheric Pad], [Beat Drop])."
    )
    
    user_prompt = (
        "Write a complete Japanese song inspired PURELY by the following reference image:\n\n"
        "Visual Concept: A neon-drenched fallen angel. The angel has contrasting wings (one dark, one light), a broken glowing halo, chains wrapped around them, and subtle fangs.\n"
        "The atmosphere is cyberpunk, neon-noir, dark but visually stunning and melancholic.\n"
        "Focus entirely on capturing the feelings of neon lights, broken divinity, chains, and this breathtakingly tragic aesthetic. Write poetic, highly evocative lyrics."
    )
    
    url = f"{DEFAULT_API_URL}/models/{DEFAULT_MODEL}:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.8, "topP": 0.95, "maxOutputTokens": 2048}
    }
    
    print("Calling Gemini API...")
    res = requests.post(url, headers=headers, json=body, timeout=120)
    if res.status_code != 200:
        print(f"Error: {res.status_code} - {res.text}")
        sys.exit(1)
        
    text = response_text(res.json())
    
    out_dir = project_root / "outputs" / "freestyle"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "pure_visual_angel.md"
    out_file.write_text(text, encoding="utf-8")
    print(f"Success! Pure visual lyrics written to {out_file}")

if __name__ == "__main__":
    run_pure_visual_song()
