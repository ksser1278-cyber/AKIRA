import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path("src").resolve()))

from akira_engine.phonetic_engine import apply_stutter_glitch

def test():
    # Test line with plenty of plosives and vowels
    # 'k' is plosive (explosive), 'a' is vowel (melodic)
    line = "過去を消して、明日を掴むんだ"
    
    print("Testing Glitch Engine (Counter Mode)...")
    
    # 1. Explosive Test
    glitched_exp = apply_stutter_glitch(line, style="explosive", intensity=1.0)
    exp_count = glitched_exp.count("-")
    
    # 2. Melodic Test
    glitched_mel = apply_stutter_glitch(line, style="melodic", intensity=1.0)
    mel_count = glitched_mel.count("-")
    
    print(f"Original: {len(line)} chars")
    print(f"Explosive dashes: {exp_count}")
    print(f"Melodic dashes: {mel_count}")
    
    if exp_count > 0 or mel_count > 0:
        print("SUCCESS: Glitches generated.")
    else:
        print("FAILURE: No glitches generated even at 1.0 intensity.")

if __name__ == "__main__":
    test()
