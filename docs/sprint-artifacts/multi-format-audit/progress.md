# Progress: Multi-Format Extraction Pipeline Audit
Date: 2026-03-14

## Completed
- [x] 1.1 Read ground truth files (alexander: 43 records/5 buildings, aldavilla: 4 records/10 buildings)
- [x] 1.2 Query SurrealDB baseline state per source
- [x] 1.3 Investigated 3980 source (20 buildings in structure, 1 in inventory)
- [x] 2.1 Triggered Alexander extraction (force=true) — COMPLETED with 0 records (file not found first attempt, then page range failure)
- [x] 2.2 Triggered Aldavilla extraction (force=true) — STUCK (see F8)
- [x] 2.3 Triggered 3980 extraction (force=true) — STUCK (see F8)
- [x] 3.1 Alexander: 10 buildings detected (should be 5), all named "Alexander District Hospital"
- [x] 3.2 Alexander: 0/43 records (complete failure — pages 5-24 missed)
- [x] 3.3 Alexander: per-row path never triggered (0 tables on pages 1-4)
- [x] 4.1 Alexander: 0/43 recall, N/A precision (no records to compare)
- [x] 5.1 Per-format findings with file:line references — COMPLETE
- [x] 5.2 Column alias coverage check — COMPLETE (6 gaps identified)
- [x] 5.3 Prompt template format sensitivity check — COMPLETE (3 prompts audited)
- [x] 5.4 Format compatibility matrix — COMPLETE (partial — Aldavilla/3980 pending)

## Blocked
- [ ] 3.4 Aldavilla building detection accuracy — extraction stuck (F8)
- [ ] 3.5 Aldavilla record count — extraction stuck (F8)
- [ ] 3.6 3980 diagnostic analysis — extraction stuck (F8)
- [ ] 4.2 Aldavilla ground truth comparison — extraction stuck (F8)
- [ ] 4.3 False negatives/positives per source — partially blocked
- [ ] 5.5 Fix recommendations — COMPLETE based on available data

## Key Findings Summary

### 11 Findings: 3 CRITICAL, 5 HIGH, 2 MEDIUM, 1 INFO

| ID | Severity | Finding | Status |
|----|----------|---------|--------|
| F1 | CRITICAL | Building names use site_name, not inventory name | **FIXED** (825d0010) |
| F2 | CRITICAL | Alexander inventory returns raw markdown rows | **FIXED** (972d7038) |
| F3 | CRITICAL | Alexander total_pages=4 (actual=24) | **FIXED** (be805d4d) |
| F4 | HIGH | Consultant detected as `<!-- image -->` | **FIXED** (7c7df01b) |
| F5 | HIGH | Aldavilla page ranges all identical (3-15) | Design only (5de788ef) |
| F6 | HIGH | 3980: 20 buildings → 1 in inventory | **FIXED** (972d7038) |
| F7 | MEDIUM | Default model phi4:14b instead of llama3.1:8b | **FIXED** (.env local) |
| F8 | HIGH | Concurrent extraction hang (40+ min) | **FIXED** (772a9b0a) |
| F9 | HIGH | Column aliases Clutch-specific only | **FIXED** (f374332b) |
| F10 | HIGH | BuildingRecord.building_name missing fallback | **FIXED** (825d0010) |
| F11 | CRITICAL | N*M record duplication for shared page ranges | Design only (5de788ef) |

### Extraction Results

| Source | Command | Status | Buildings | Records | Duration |
|--------|---------|--------|-----------|---------|----------|
| Alexander | geza6d81 | Completed | 10 (wrong) | 0 ❌ | 853s |
| Aldavilla | ie2pge2f | **STUCK** | 10 (correct count) | 0 | 40+ min |
| 3980 | axl8yv96 | **STUCK** | 1 (wrong) | 0 | 40+ min |
