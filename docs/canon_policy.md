# Canon Admission Policy

## Overview

The AKIRA ENGINE uses a **3-stage gate** for canon admission:

| Stage | Meaning |
|-------|---------|
| **PASS** | Track admitted to canon immediately |
| **WARN** | Track admitted with warnings logged |
| **HOLD** | Track held for manual review; not admitted |
| **REJECT** | Track blocked from canon |

## Admission Criteria

### Quality (Craft)
- **PASS**: `craft_score >= 80`
- **HOLD**: `75 <= craft_score < 80`
- **REJECT**: `craft_score < 75`

### Grounding
- **PASS**: `grounding_intensity >= 0.7`
- **WARN**: `0.6 <= grounding < 0.7`
- **HOLD**: `grounding < 0.6`

### Originality
- **PASS**: `composite_originality >= 0.5`
- **HOLD**: `0.3 <= originality < 0.5`
- **REJECT**: `originality < 0.3`

### Cliché Density
- **WARN**: `cliche_density > 0.2`

## Diversity Constraints (Recent 100 Hard Cap)

| Constraint | Limit | Type |
|-----------|-------|------|
| Cluster quota | 25% of recent 100 | Hard cap |
| Hook grammar continuity | Max 3 consecutive | Hard cap |
| Recency distance | 80% motif overlap with last 5 | Hard cap |
| Underrepresented cluster | +5 craft bonus if < 5% | Soft bonus |

## Rejection Reason Codes

| Code | Meaning |
|------|---------|
| `low_craft_score` | Below minimum craft threshold |
| `low_grounding_intensity` | Insufficient artist grounding |
| `low_originality` | Too similar to existing corpus |
| `high_cliche_density` | Too many common expressions |
| `high_imitation_risk` | Too close to specific artist |
| `cluster_quota_exceeded` | Cluster overrepresented in recent canon |
| `recent_canon_too_close` | Near-duplicate of recent admission |
| `hook_grammar_continuity_limit` | Same hook pattern used too often |

## Audit Trail

All admission evaluations are logged to `outputs/admission_log.jsonl` with:
- Track ID, status, reason codes, craft score, originality score
