from __future__ import annotations

import random
import hashlib
from typing import Any
from ..demo_renderer import _artist_imagery_defaults, _artist_pre_lines, _artist_verse_lines, _artist_chorus_lines, _artist_bridge_lines, _artist_final_lines, _artist_outro_lines, _surface_rewrite

def _generative_section_lines(section: str, hook: str, a: str, b: str, c: str) -> list[str]:
    """Production path: Clean, non-template-heavy lines."""
    if section == "intro": return [f"{a}を数えるほど", f"{b}じゃ足りない", f"ねえ {hook}の外で"]
    if "verse" in section: return [f"{a}ばかり増えて", f"{b}の奥で", f"{c}ひとつで救われる", "笑っているうちに"]
    if "chorus" in section: return [f"{hook} {hook}", f"{a}まで本音にして", f"{b}より先に", "ねえ まともなふりはもういい"]
    if section == "bridge": return [f"{a}に合わせた", f"{b}の外側に", f"せめて {hook}だけは"]
    if section == "outro": return [f"{a}의 余熱で", f"{hook}を見失わず"]
    return [f"{hook} ..."]

def run_renderer_stage(
    plan: dict[str, Any],
    *,
    variant_index: int,
    scaffold_mode: bool = False,
) -> dict[str, Any]:
    """Execute Stage H: Renderer (Path-Separated Version)."""
    artist_id = str(plan.get("artist_id", "default")).strip()
    mode_id = str(plan.get("mode_id", "default")).strip()
    hook = str(plan.get("hook_blueprint", {}).get("core_text", "...")).strip()
    
    rng = random.Random(int(hashlib.md5(f"{plan['track_id']}:{variant_index}".encode("utf-8")).hexdigest()[:8], 16))
    
    # Generic motifs if none exist
    a, b, c = ("視線", "喉", "体温")
    
    lines = [f"# {hook}", ""]
    for card in plan.get("section_cards", []):
        section = str(card.get("section", "")).strip()
        lines.append(f"[{section}]")
        
        if scaffold_mode:
            # Use original artist-specific templates
            if section == "intro": sl = _artist_pre_lines(artist_id, mode_id, hook, a, b)
            elif "verse" in section: sl = _artist_verse_lines(artist_id, mode_id, hook, a, b, c)
            elif section == "bridge": sl = _artist_bridge_lines(artist_id, mode_id, hook, a, b)
            elif "chorus" in section: sl = _artist_chorus_lines(artist_id, mode_id, hook, a, b)
            elif "final" in section: sl = _artist_final_lines(artist_id, mode_id, hook, a, b)
            elif "outro" in section: sl = _artist_outro_lines(artist_id, mode_id, hook, a)
            else: sl = _artist_chorus_lines(artist_id, mode_id, hook, a, b)
        else:
            # Production: Clean generative path
            sl = _generative_section_lines(section, hook, a, b, c)

        # Apply shaping only if in scaffold mode (to keep production pure)
        artist_for_surface = artist_id if scaffold_mode else "default"
        lines.extend(_surface_rewrite(sl, artist_for_surface, rng))
        lines.append("")

    return {
        "candidate_id": f"{plan['track_id']}-candidate-{variant_index + 1}",
        "title": hook,
        "markdown": "\n".join(lines).strip() + "\n",
        "scaffold_mode": scaffold_mode
    }
