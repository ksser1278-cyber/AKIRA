from dataclasses import dataclass, field

@dataclass(frozen=True)
class ProductionPolicy:
    """
    Fixed rules for the AKIRA ENGINE Production Lane.
    These values are frozen as the official vNext baseline.
    Any changes require a formal roadmap update.
    """
    # Linguistic Purity (Critic/Hard Gate)
    JAPANESE_RATIO_MIN: float = 0.88
    LATIN_TOKEN_RATIO_MAX: float = 0.15
    REJECT_HALI_HALLUCINATION: bool = True # Suppress LLM Critic false positives
    
    # Grounding (Bridge)
    MANDATORY_SENSORY_ANCHORS: bool = True
    IMAGERY_COVERAGE_HARD_FAIL_THRESHOLD: float = 0.0
    RETRY_ON_IMAGERY_FAILURE: bool = True
    
    # Provenance (Guard)
    EXCLUDE_PROVISIONAL_SOURCES: bool = True
    GOLD_SOURCE_REQUIRED_FOR_GROUNDING: bool = True
    
    # Execution
    MAX_RETRIES: int = 1
    ADAPTIVE_BATCHING: bool = True # Base 3-5, Hard 11
    
    # Selection (Committee)
    GOLD_SCORE_THRESHOLD: float = 90.0
    SILVER_SCORE_THRESHOLD: float = 80.0
    
    # Schema Version
    PRODUCTION_SCHEMA_VERSION: str = "2.0"

# Canonical Instance
BASELINE_2026_03_31 = ProductionPolicy()
