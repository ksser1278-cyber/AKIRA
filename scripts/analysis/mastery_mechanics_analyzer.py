import json
import math
import statistics
import sys
from pathlib import Path
from collections import Counter
import re

# Force UTF-8 for console output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path for akira_engine imports
sys.path.append(str(Path("src").resolve()))
from akira_engine.japanese_lyric_features import mora_unit_estimate

COHORTS_DIR = Path("datasets/analysis")
REPORTS_DIR = Path("reports/mastery")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Vowel Detection
VOWELS = "aiueo"
KANA_VOWELS = {
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    'か': 'a', 'き': 'i', 'く': 'u', 'け': 'e', 'こ': 'o',
    'さ': 'a', 'し': 'i', 'す': 'u', 'せ': 'e', 'そ': 'o',
    'た': 'a', 'ち': 'i', 'つ': 'u', 'て': 'e', 'と': 'o',
    'な': 'a', 'に': 'i', 'ぬ': 'u', 'ね': 'e', 'の': 'o',
    'は': 'a', 'ひ': 'i', 'ふ': 'u', 'へ': 'e', 'ほ': 'o',
    'ま': 'a', 'み': 'i', 'む': 'u', 'め': 'e', 'も': 'o',
    'や': 'a', 'ゆ': 'u', 'よ': 'o',
    'ら': 'a', 'り': 'i', 'る': 'u', 'れ': 'e', 'ろ': 'o',
    'わ': 'a', 'を': 'o', 'ん': 'n'
}
# Plosives/Impact Consonants
PLOSIVES = r"[かきくけこがぎぐげこたぢつてとだぢづでどぱぴぷぺぽkptgdbq]"

def get_vowel_profile(text):
    vowels = []
    for char in text:
        if char in KANA_VOWELS:
            vowels.append(KANA_VOWELS[char])
    return Counter(vowels)

def get_phonetic_impact(text):
    matches = re.findall(PLOSIVES, text)
    return len(matches) / max(1, len(text))

def analyze_cohort(name, path):
    results = {
        "mora_density": [],
        "line_variance": [],
        "repetition_index": [],
        "phonetic_impact": [],
        "hook_latency": [],
        "vowel_dominance": Counter(),
        "chorus_mora": []
    }
    
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                track = json.loads(line)
                sections = track.get("structural_profile", {}).get("section_features", [])
                lyrics = track.get("lyrics", "")
                
                # Global metrics
                # Hook Latency (Line index of first chorus)
                lines = lyrics.splitlines()
                chorus_idx = -1
                for i, l in enumerate(lines):
                    if "[Chorus]" in l or "[sabi]" in l or "Chorus" in l:
                        chorus_idx = i
                        break
                if chorus_idx != -1:
                    results["hook_latency"].append(chorus_idx)
                
                # Sectional metrics
                for sec in sections:
                    sec_name = sec.get("section_name", "").lower()
                    sec_type = sec.get("jp_section_role", "")
                    
                    # Extract section text from lyrics if possible, 
                    # but refined corpus might not have text per section.
                    # We might need to split lyrics by [Section] tags.
                    
                    # For now, use the 'mora_density' label if available, 
                    # or calculate from profile if we have it.
                    # WAIT: The refined corpus HAS the profile.
                    
                # Let's extract section text for more accurate analysis
                sec_texts = re.split(r'\[.*?\]', lyrics)
                sec_texts = [t.strip() for t in sec_texts if t.strip()]
                
                for i, text in enumerate(sec_texts):
                    lines_in_sec = text.splitlines()
                    mora_counts = [mora_unit_estimate(l) for l in lines_in_sec]
                    if not mora_counts: continue
                    
                    avg_mora = sum(mora_counts) / len(mora_counts)
                    var_mora = statistics.stdev(mora_counts) if len(mora_counts) > 1 else 0
                    
                    # Repetition Index (unique lines vs total lines)
                    unique_lines = len(set(lines_in_sec))
                    rep_idx = 1 - (unique_lines / len(lines_in_sec))
                    
                    impact = get_phonetic_impact(text)
                    
                    results["mora_density"].append(avg_mora)
                    results["line_variance"].append(var_mora)
                    results["repetition_index"].append(rep_idx)
                    results["phonetic_impact"].append(impact)
                    
                    # Vowel and Mora for Chorus Specifically
                    # Heuristic: the first few sections are likely Chorus if they are dense
                    # Better: map back to structural_profile roles.
                    # The refined corpus has section_features.
                    if i < len(sections):
                        role = sections[i].get("jp_section_role", "")
                        if role == "sabi" or role == "dai_sabi":
                            results["chorus_mora"].append(avg_mora)
                            results["vowel_dominance"].update(get_vowel_profile(text))
                            
            except Exception as e:
                continue
                
    # Normalize results
    summary = {
        "avg_mora": safe_mean(results["mora_density"]),
        "avg_variance": safe_mean(results["line_variance"]),
        "avg_repetition": safe_mean(results["repetition_index"]),
        "avg_impact": safe_mean(results["phonetic_impact"]),
        "avg_hook_latency": safe_mean(results["hook_latency"]),
        "chorus_mora": safe_mean(results["chorus_mora"]),
        "top_vowels": results["vowel_dominance"].most_common(5)
    }
    return summary

def safe_mean(data):
    return sum(data) / len(data) if data else 0

def main():
    print("Mastery Mechanics Analysis Starting...")
    report = {}
    
    for cohort in ["elite", "mid", "control"]:
        path = COHORTS_DIR / f"cohort_{cohort}.jsonl"
        print(f" -> Analyzing {cohort}...")
        report[cohort] = analyze_cohort(cohort, path)
        
    # Calculate Lift (Elite vs Control)
    lift = {}
    for key in report["elite"]:
        if isinstance(report["elite"][key], (int, float)):
            e_val = report["elite"][key]
            c_val = report["control"][key]
            lift[key] = (e_val / c_val - 1) if c_val != 0 else 0
            
    # Save Report
    final_report = {
        "raw": report,
        "lift": lift
    }
    (REPORTS_DIR / "analysis_summary.json").write_text(json.dumps(final_report, indent=4), encoding="utf-8")
    
    # Generate Markdown Summary
    md = "# Mastery Mechanics: Cohort Analysis\n\n"
    md += "| Metric | Elite | Mid | Control | Lift (E/C) |\n"
    md += "| :--- | :--- | :--- | :--- | :--- |\n"
    for key in lift:
        md += f"| {key} | {report['elite'][key]:.3f} | {report['mid'][key]:.3f} | {report['control'][key]:.3f} | {lift[key]:.1%} |\n"
    
    md += "\n## Vowel Dominance (Chorus)\n"
    for c in ["elite", "mid", "control"]:
        vowels = ", ".join([f"{v}: {n}" for v, n in report[c]["top_vowels"]])
        md += f"- **{c}**: {vowels}\n"
        
    (REPORTS_DIR / "analysis_summary.md").write_text(md, encoding="utf-8")
    print(f"Analysis Complete. Reports saved to {REPORTS_DIR}")

if __name__ == "__main__":
    main()
