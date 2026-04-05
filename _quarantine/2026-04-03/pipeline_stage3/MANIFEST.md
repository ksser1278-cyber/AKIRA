# Pipeline Stage 3 Quarantine

Moved on `2026-04-03`.

## Purpose

Reduce the active `scripts/pipeline` surface to rebuild-relevant tooling only.

## Quarantined Families

- generation safety
- round2
- mode support
- producer expansion
- hard case

## Rationale

These scripts belong to older expansion, promotion, and evaluation workflows that are not part of the current reduced rebuild surface.

They were moved, not deleted.
