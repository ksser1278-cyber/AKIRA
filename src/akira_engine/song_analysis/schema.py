from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class EvidenceStatus(StrEnum):
    VERIFIED = "VERIFIED"
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    HYPOTHESIS = "HYPOTHESIS"


LYRIC_FUNCTION_TAGS = [
    "persona_declaration",
    "desire_statement",
    "self_diagnosis",
    "target_address",
    "emotional_reversal",
    "emotional_signal",
    "hook_phrase",
    "phonetic_hook",
    "judgment_phrase",
    "obsessive_leakage",
    "vulnerability",
    "comic_relief",
    "violence_or_rejection",
    "scene_image",
    "title_reference",
    "rhythm_filler",
]


@dataclass(frozen=True)
class Claim:
    choice: str
    reason: str
    effect: str
    reuse_method: str
    evidence: list[str]
    confidence: float
    status: EvidenceStatus

    def to_dict(self) -> dict[str, Any]:
        return {
            "choice": self.choice,
            "reason": self.reason,
            "effect": self.effect,
            "reuse_method": self.reuse_method,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
            "status": self.status.value,
        }


def claim(
    *,
    choice: str,
    reason: str,
    effect: str,
    reuse_method: str,
    evidence: list[str],
    confidence: float,
    status: EvidenceStatus,
) -> dict[str, Any]:
    return Claim(
        choice=choice,
        reason=reason,
        effect=effect,
        reuse_method=reuse_method,
        evidence=evidence,
        confidence=confidence,
        status=status,
    ).to_dict()
