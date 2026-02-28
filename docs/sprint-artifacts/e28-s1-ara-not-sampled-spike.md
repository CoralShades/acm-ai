# Story E28-S1: ARA "Not Sampled" Research Spike

**Epic**: E28 — Alexander "Not Sampled" Recovery
**Priority**: P1
**Status**: done
**Size**: S (1 SP)
**Depends On**: E27-S4 done, E26-S7 done

## User Story

As a developer improving Alexander extraction accuracy,
I want to understand exactly why 14+ "Not Sampled" records are missed in
ARA-format documents,
So that E28-S2 can implement a targeted, evidence-based fix.

## Acceptance Criteria

- [x] All 17 missing "Not Sampled" records identified by building, room, and item
- [x] ARA "Not Sampled" text patterns documented with PDF evidence
- [x] Root cause confirmed: SAMP-only regex + no Docling injection
- [x] Fix strategy recommended with specific files to change
- [x] Spike output written to docs/research/e28-s1-ara-spike.md

## Outputs

- docs/research/e28-s1-ara-spike.md
- scripts/research/e28_s1_gap_analysis.py
