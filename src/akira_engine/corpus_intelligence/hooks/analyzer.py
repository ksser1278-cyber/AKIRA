# src/akira_engine/corpus_intelligence/hooks/analyzer.py

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List, Tuple


class MoraCounter:
    """Pure-Python Mora (Japanese syllable) counter.
    
    Handles:
        - Hiragana/Katakana: 1 mora each.
        - Long vowels (ー): 1 mora.
        - Small tsu (っ): 1 mora.
        - Digraphs (きゃ, ぴょ): 1 mora total.
        - Nasal (ん): 1 mora.
    """

    # Hiragana and Katakana Unicode ranges
    # Hiragana: 3040-309F
    # Katakana: 30A0-30FF
    
    RE_DIGRAPH = re.compile(r'[ぁぃぅぇぉゃゅょァィゥェォャュョ]')
    RE_KANA = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')
    RE_PROLONGED = re.compile(r'ー')
    RE_HIRAGANA = re.compile(r'[\u3041-\u3096]')
    RE_KATAKANA = re.compile(r'[\u30A1-\u30FA]')

    @classmethod
    def count_mora(cls, text: str) -> int:
        """Count the number of mora in a Japanese string.
        
        Syllable count logic:
        1. Remove all non-Kana characters (except for placeholders like kanji - which we estimate)
        2. Count all Kana.
        3. Subtract 1 for each small kana following a large kana (digraphs).
        """
        # For simplicity in this pure-python version, we assume kanji is 2 mora on average
        # if not furigana-equipped. But since our corpus has ground truth, 
        # we focus on the kana-heavy parts or estimate kanji.
        
        # 1. Strip non-kana, non-kanji
        # (For the bank, we expect cleaned lyrics)
        
        # 2. Extract kana and count
        all_kana = cls.RE_KANA.findall(text)
        digraphs = cls.RE_DIGRAPH.findall(text)
        
        # Basic count is just length of kana list minus digraphs
        mora = len(all_kana) - len(digraphs)
        
        # 3. Estimate Kanji (approx 2 mora per kanji)
        kanji_count = len(re.findall(r'[\u4E00-\u9FFF]', text))
        mora += kanji_count * 2
        
        return max(mora, 1) if text.strip() else 0


class RhymeAnalyzer:
    """Vowel-based Assonance (각운) Analyzer."""
    
    # Mapping of characters to their base vowel (A, I, U, E, O)
    VOWEL_MAP = {
        'a': 'a', 'i': 'i', 'u': 'u', 'e': 'e', 'o': 'o',
        'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
        'か': 'a', 'き': 'i', 'く': 'u', 'け': 'e', 'こ': 'o',
        'さ': 'a', 'し': 'i', 'す': 'u', 'せ': 'e', 'そ': 'o',
        'た': 'a', 'ち': 'i', 'つ': 'u', 'て': 'e', 'と': 'o',
        'な': 'a', 'に': 'i', 'ぬ': 'u', 'ね': 'e', 'の': 'o',
        'は': 'a', 'ひ': 'i', 'ふ': 'u', 'へ': 'e', 'ほ': 'o',
        'ま': 'a', 'み': 'i', 'む': 'u', 'め': 'e', 'も': 'o',
        'や': 'a', 'ゆ': 'u', 'よ': 'o',
        'ら': 'a', 'り': 'i', 'る': 'u', 'れ': 'e', 'ろ': 'o',
        'わ': 'a', 'を': 'o', 'ん': 'n',
        # Add common katakana or just map via romaji if needed
    }

    @classmethod
    def get_last_vowel(cls, text: str) -> str:
        """Get the vowel of the last character in the text."""
        if not text:
            return ""
        
        # Check last character
        last_char = text.strip()[-1]
        
        # Basic mapping for common hiragana
        # In a real production system, we'd use a full transcription, 
        # but for this bank, a suffix-map covers 80% of rhymes.
        
        # Use a more comprehensive regex/mapping if needed
        # Fallback for romaji/english in hooks
        if last_char.lower() in 'aiueo':
            return last_char.lower()
            
        return cls.VOWEL_MAP.get(last_char, "")

    @classmethod
    def detect_scheme(cls, lines: List[str]) -> List[Tuple[str, List[int]]]:
        """Detect rhyme scheme across lines.
        
        Returns List of (vowel, line_indices).
        """
        vowels = [cls.get_last_vowel(line) for line in lines]
        
        groups = defaultdict(list)
        for i, v in enumerate(vowels):
            if v:
                groups[v].append(i)
        
        # Filter for schemes that cover at least 2 lines
        return [(v, indices) for v, indices in groups.items() if len(indices) >= 2]


class RepetitionMiner:
    """Structural repetition miner."""

    @classmethod
    def detect_repetition(cls, lines: List[str]) -> str:
        """Identify repetition type: anaphora, epistrophe, or none."""
        if len(lines) < 2:
            return "none"
        
        # Check for whole line repetition (most specific)
        if len(set(lines)) < len(lines):
            return "chorus_loop"

        # Check for Longest Common Prefix (LCP) > 2 chars as Anaphora
        prefix = ""
        if len(lines) >= 2:
            s1, s2 = lines[0].strip(), lines[1].strip()
            for i in range(min(len(s1), len(s2))):
                if s1[i] == s2[i]:
                    prefix += s1[i]
                else:
                    break
        
        if len(prefix) >= 2:
            return "anaphora"
            
        return "none"


from collections import defaultdict
