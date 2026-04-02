# AKIRA ENGINE: 90-Day Operational Roadmap (Final Approved Version)

This roadmap formalizes the transition of AKIRA ENGINE from an experimental songwriting system into a professional **Production Factory**.

The strategic shift is now complete:
we are moving from **feature development** to **system operationalization**.

---

## Strategic Decisions (Approved)

### 1. Delta Update Migration
Delta updates are included in the 90-day plan.

However, the scope for this roadmap is:
- **architecture design,**
- **pilot implementation,**
- **partial operational rollout**

—not a full migration of the entire 60k+ Alexandria library within this window.

### 2. Local LLM Fallback Policy
Local LLM fallback is approved only for the **Research Lane** and for **non-critical generation paths**.

It is **not permitted** for:
- final production candidates,
- critic scoring,
- pre-audit judgment,
- promotion decisions,
- Gold-tier bundle outputs.

Production-grade final outputs must remain on the high-trust path.

---

# Phase 1: Baseline Freeze & Canonicalization (Days 0-30)

**Goal**: Lock the current high-performance logic as the official Production baseline and establish the Stage-based architecture as the canonical engine.

## A. Production Baseline Freeze
- [ ] Freeze the following rules as Production standard:
  - `honest_metrics`
  - `provenance_guard`
  - `hard_gate`
  - `retry_logic`
  - `atlas_v2_grounding`
  - `promotion_rules`
- [ ] Allow only critical bug fixes in the Production lane.
- [ ] Disallow experimental logic changes in the frozen baseline.

## B. Stage Canonicalization
- [ ] Declare the following Stage modules as the official vNext engine:
  - `normalize`
  - `features`
  - `conditioning`
  - `pre_audit`
  - `planner`
  - `critic`
  - `promotion`
- [ ] Refactor:
  - `demo_runtime.py`
  - `demo_planner.py`
  - `demo_critic.py`
  
  into thin compatibility wrappers around the Stage modules.
- [ ] Ensure new logic is added only to Stage modules, not to `demo_*` files.

## C. Production Schema Freeze
- [ ] Standardize per-track production artifacts:
  - `selected_lyric.md`
  - `run_manifest.json`
  - `critic_results.json`
  - `conditioning_record.json`
  - `pre_audit_result.json`
  - `promotion_result.json`
- [ ] Add schema validation for all production outputs.

---

# Phase 2: Elite Factory Construction (Days 31-60)

**Goal**: Convert Elite 100 synthesis from a project workflow into a repeatable production line.

## A. Adaptive Candidate Batching
- [ ] Replace fixed batching with **adaptive batching**:
  - stable slots: 3-5 candidates
  - difficult slots: up to 11 candidates
  - high-retry artist/mode combinations: expanded candidate sets
- [ ] Keep all final production synthesis in **Production Path** only.

## B. Selection Committee Formalization
- [ ] Formalize promotion statuses:
  - `Gold`
  - `Silver`
  - `Hold`
  - `Fail`
- [ ] Promotion must consider:
  - Grounding Coverage
  - Purity
  - Structural Integrity
  - Singability
  - Motif Binding
  - Diversity
  - Provenance Safety

## C. Packaging Automation
- [ ] Automate bundle exports:
  - `elite_manifest.json`
  - `ranking.csv`
  - `source_provenance_report.json`
  - `elite_summary.md`

## D. Diversity Control
- [ ] Enforce artist/mode diversity caps.
- [ ] Prevent over-selection of near-duplicate outputs.

## E. Atlas v2 Production Integration
- [ ] Make `atlas_v2_trusted` the default grounding reference in Planner.

---

# Phase 3: Dataset Productization (Days 61-90)

**Goal**: Convert production outputs into training-grade and evaluation-grade data products.

## A. Data Packaging
- [ ] Export training-ready JSONL variants with full audit lineage.

## B. Hybrid Lane Split
- [ ] Finalize the split between **Production Lane** (Stable) and **Research Lane** (Experimental).

## C. Delta Update Pilot
- [ ] Introduce source fingerprinting and pilot incremental atlas refresh.

## D. Operational Audit Layer
- [ ] Track fail rates, retry rates, and imagery coverage averages.

---

# Final Operational Definition

**AKIRA ENGINE = Production Engine + Promotion Engine + Bundle Factory + Dataset Packager**
