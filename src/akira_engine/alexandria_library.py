import json
import random
from pathlib import Path
from typing import Any, List, Dict

class AlexandriaLibrary:
    """
    The 'Library of Alexandria' inspiration layer.
    Allows the engine to draw from 10,000+ high-fidelity Vocaloid tracks.
    """
    def __init__(self, index_path: str = "data/_global/styles/alexandria_style_index.json"):
        self.index_path = Path(index_path)
        self.data: Dict[str, Any] = {}
        self._load_library()

    def _load_library(self):
        if not self.index_path.exists():
            print(f"[ALEXANDRIA] Warning: Index not found at {self.index_path}")
            return
        try:
            self.data = json.loads(self.index_path.read_text(encoding="utf-8"))
            count = self.data.get("metadata", {}).get("total_indexed", 0)
            print(f"[ALEXANDRIA] Loaded {count} tracks into the inspiration layer.")
        except Exception as e:
            print(f"[ALEXANDRIA] Error loading library: {e}")

    def get_motifs_for_model(self, model_name: str, limit: int = 5) -> List[str]:
        """
        Retrieves random motifs from the specified model cluster (Model_A_Staccato_Speed, etc.)
        """
        clusters = self.data.get("clusters", {})
        # Mapping generic model names to index keys
        cluster_key = model_name
        if "staccato" in model_name.lower(): cluster_key = "Model_A_Staccato_Speed"
        elif "humanoid" in model_name.lower(): cluster_key = "Model_B_Humanoid_Pop"
        elif "bass" in model_name.lower(): cluster_key = "Model_C_Bass_Glitch"

        items = clusters.get(cluster_key, [])
        if not items:
            # Fallback to all items if cluster is empty
            items = [item for c in clusters.values() for item in c]
        
        if not items:
            return []

        selection = random.sample(items, min(len(items), limit * 2))
        motifs = []
        for s in selection:
            motifs.extend(s.get("tags", []))
        
        # Dedupe and return limit
        unique_motifs = list(dict.fromkeys(motifs))
        random.shuffle(unique_motifs)
        return unique_motifs[:limit]

    def get_structural_hint(self, model_name: str) -> str:
        """
        Returns a structural 'Thinking Hint' based on the cluster's common patterns.
        """
        if "staccato" in model_name.lower():
            return "Emulate high-mora density with irregular rhythmic stutters and percussive phrasing."
        elif "humanoid" in model_name.lower():
            return "Focus on breathy, emotional phrasing with clear melodic release in the Sabi."
        return "Focus on rhythmic repetition and urban, glitch-heavy motifs."
