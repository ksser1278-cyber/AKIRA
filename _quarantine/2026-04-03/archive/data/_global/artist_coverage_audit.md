# Artist Coverage Audit

This document evaluates the practical readiness of artist archetypes for the AKIRA ENGINE demo pipeline (Planner / Renderer / Critic).

## 1. Readiness Summary

| Readiness | Count | Description |
| :--- | :---: | :--- |
| **Ready** | 2 | Canonical JSON present, mode support verified, low risk. |
| **Partial** | 6 | Canonical JSON present, but renderer-level verification or specific phrase banks are missing. |
| **Not Ready** | 3 | Missing canonical JSON or record elevation (Round 2 data). |

## 2. Core 8 Coverage Matrix

| Artist ID | JSON | Mode Support | Renderer Readiness | Evidence Basis | Key Blocker |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **DECO*27** | Yes | Yes | **Ready** | Canonical json exists; baseline smoke results available. | - |
| **PinocchioP** | Yes | Yes | **Ready** | Canonical json exists; baseline smoke results available. | - |
| **Kanaria** | Yes | Yes | Partial | Mode support (EYE, KING) exists; no verified smoke test output. | Artist-specific phrase bank integration pending. |
| **Kairiki Bear** | Yes | Yes | Partial | Round2 records (Ruma) exist; jitter in repetitive mora unverified. | Stutter pre-hook logic jitter in renderer. |
| **MARETU** | Yes | Yes | Partial | Canonical json exists; Suji record exists; no verified smoke test output. | Renderer lacks explicit polite-cruel phrase shaping. |
| **Iyowa** | Yes | Yes | Partial | Canonical json exists; Kyu-kurarin record exists; no verified smoke test output. | Renderer-specific imagery shaping is limited. |
| **Syudou** | Yes | Yes | Partial | BCD grounding successful; clear diagnostic label rules. | Diagnostic interjection density unstandardized. |
| **Neru** | Yes | Yes | Partial | Enforces industrial tool patterns; TTTeddy Bear grounded. | Surgical-industrial tool bank integration pending. |

## 3. High-Value Expansion Candidates

| Artist ID | JSON | Mode Support | Renderer Readiness | Priority | Recommended Next Action |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **VIVINOS** | No | Yes | Not Ready | High | Upgrade to canonical MD+JSON (Korean-fusion). |
| **Eve** | No | Yes | Not Ready | Medium | Abstract storytelling-pop structure into JSON. |
| **Giga** | No | Yes | Not Ready | Medium | Define EDM-staccato flags in canonical JSON. |

## 4. Technical Observations

### A. Data-to-Engine Gap

While the **Core 8** have structurally stable JSON archetypes, the **Demo Renderer** still has uneven artist-specific phrase shaping. Most "Partial" ratings reflect missing or unverified surface behavior during generation.

### B. Evidence-Based Assessment

Readiness is judged not just on the existence of data, but on whether the current renderer behavior has been verified. Artists with "Partial" status require a verified smoke test to move to "Ready."

### C. Policy Alignment

All Ready/Partial archetypes now follow the strict conservative flags (safe_for_lexical_sampling = false), ensuring that the engine must derive stylistic rules rather than simply sampling verbatim text.

---

**Audit Status:** Active
**Last Updated:** 2026-03-22
**Next Milestone:** Finalize Demo Smoke Test Matrix
