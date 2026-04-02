import re
from typing import List, Dict, Any, Optional

# Regular expression for Korean characters (Hangul)
# Covers Syllables, Jamo, and compatibility Jamo
HANGUL_REGEX = re.compile(r'[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F\uA960-\uA97F\uD7B0-\uD7FF]')

# Regular expression for allowed J-Pop characters
# Hiragana, Katakana, Kanji, Romaji, Numbers, and common Punctuation
# Includes Full-width variants, iteration marks (々), and Markdown headers (#)
ALLOWED_CHARS_REGEX = re.compile(r'^[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3005a-zA-Z0-9\s\.,!\?\(\)\[\]\'\"\-\~\*\:\;\/\u3000-\u303F\uFF01-\uFF5E#]+$')

def lint_mastery_output(markdown: str, mode_id: str = "universal") -> Dict[str, Any]:
    """
    Performs a comprehensive 'Final Publish' quality check on generated lyrics.
    Returns a dict with 'is_valid' and 'reasons'.
    """
    reasons = []
    lines = [l.strip() for l in markdown.splitlines() if l.strip()]
    
    if not lines:
        return {"is_valid": False, "reasons": ["Empty output"]}

    # 1. Linguistic Purity Check (No Hangul)
    if HANGUL_REGEX.search(markdown):
        reasons.append("Hangul contamination detected (Linguistic Leakage)")

    # 2. Character Set Validation
    # We ignore the [Section] lines for character set as they are controlled
    for i, line in enumerate(lines):
        if line.startswith("[") and line.endswith("]"):
            continue
        
        # Experimental mode allows for some 'glitch' characters (like ∀)
        if mode_id == "glitch_hyper_pop" or "experimental" in mode_id:
             # Allow some glitch symbols
             clean_line = re.sub(r'[∀∂∇∆∏∑√∞∠∩∪∫≃≅≈≠≡≤≥]', '', line)
        else:
             clean_line = line

        if not ALLOWED_CHARS_REGEX.match(clean_line):
            # Identify the offending characters for reporting
            offenders = "".join(set(c for c in clean_line if not ALLOWED_CHARS_REGEX.match(c)))
            reasons.append(f"Invalid characters at line {i+1}: {offenders}")

    # 3. Structural Integrity (Section Tags)
    sections = [l for l in lines if l.startswith("[") and l.endswith("]")]
    if not sections:
        reasons.append("No valid section tags found (Structural Failure)")
    
    # 4. Phonetic Stutter Consistency
    # Check for malformed dashes (e.g., word endings with dangling dashes)
    if re.search(r'[ァ-ヶ]-[\s\.]', markdown) or re.search(r'[\s]-', markdown):
        # We allow 'd-d-' but not 'ta -'
        if not re.search(r'[a-zA-Z]-[a-zA-Z]', markdown):
             reasons.append("Malformed phonetic stutter detected (Phonetic Invalid)")

    # 5. Length Check
    if len(lines) < 10:
        reasons.append("Output too short for a full track (Length Failure)")

    return {
        "is_valid": len(reasons) == 0,
        "reasons": reasons,
        "mode_id": mode_id,
        "line_count": len(lines)
    }

if __name__ == "__main__":
    test_ok = "[Intro]\nさよならの歌を\n[Chorus]\n歌って、笑って、泣いて。"
    test_fail_ko = "[Intro]\n안녕\n[Chorus]\n歌って。"
    test_fail_char = "[Intro]\nHello! 😊\n[Chorus]\n歌って。"

    print(f"Test OK: {lint_mastery_output(test_ok)}")
    print(f"Test KO: {lint_mastery_output(test_fail_ko)}")
    print(f"Test Emoji: {lint_mastery_output(test_fail_char)}")
