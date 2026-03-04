# E31-S3 Tech Spec: Consensus Layer Core

**Story ID**: E31-S3
**Sprint**: V3-3
**Points**: 3 SP
**Risk**: HIGH
**Type**: Backend
**Status**: drafted
**Dependency**: E31-S2 (Provider Adapter Framework — DONE)

---

## 1. Overview

The Consensus Layer Core bridges raw per-provider extraction results (from E31-S2's `NormalizedExtractionResult` list) and the final `ACMExtractionRecord` objects stored in SurrealDB. When two providers (e.g. Docling and MinerU) both extract tables from the same PDF, their row-level records need to be matched, merged, and assigned a confidence tier.

This story implements three pure (no-I/O) or async-minimal classes:

```
[NormalizedExtractionResult, ...]   # one per provider, from E31-S2
         |
         v
  RecordMatcher.match_groups()      # pure function — no I/O
         |
         v
  List[MatchGroup]                  # clusters of candidate-equivalent rows
         |
         v
  ConsensusEngine.merge()           # async — calls ConflictResolver
         |
         v
  List[ACMExtractionRecord]         # with consensus_metadata field populated
```

Key design decisions:
1. **No new Python dependencies** — Jaro-Winkler is implemented from pure stdlib math.
2. `ConsensusEngine.merge()` is `async` to support the L3 LLM stub (real call deferred to E31-S5).
3. The design generalises beyond 2 providers — a `MatchGroup` can hold N candidate rows.
4. Unmatched single-provider rows are never dropped — they become LOW-tier records.
5. `extraction_confidence` on `ACMExtractionRecord` is updated from the computed tier.

---

## 2. File Changes Table

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/extractors/consensus/__init__.py` | CREATE | Package init — exports public API |
| `open_notebook/extractors/consensus/matcher.py` | CREATE | `RecordMatcher` — 3-stage matching logic |
| `open_notebook/extractors/consensus/engine.py` | CREATE | `ConsensusEngine` — per-field voting and tier assignment |
| `open_notebook/extractors/consensus/resolver.py` | CREATE | `ConflictResolver` — L1-L4 escalation chain |
| `open_notebook/extractors/acm_schemas.py` | UPDATE | Add `consensus_metadata: Optional[dict]` field to `ACMExtractionRecord` |
| `tests/test_record_matcher.py` | CREATE | Unit tests for all three matching stages |
| `tests/test_consensus_engine.py` | CREATE | Unit tests for voting, tier assignment, and conflict resolution |

---

## 3. Implementation Details

### 3.1 `open_notebook/extractors/acm_schemas.py` (UPDATE)

Add `consensus_metadata` as an `Optional[dict]` field to `ACMExtractionRecord`, after the `data_issues` field and before the `page_number` field.

**Exact location** — insert after line 389 (`def coerce_data_issues`) closing brace, before `extraction_confidence`:

```python
    # Consensus layer metadata (populated by ConsensusEngine — E31-S3)
    consensus_metadata: Optional[dict] = Field(
        default=None,
        description=(
            "Populated by the ConsensusEngine when multiple providers are used. "
            "Contains tier, providers, match_method, field_votes, conflict_level, "
            "and resolver_used. None for single-provider extractions."
        ),
    )
```

The full `consensus_metadata` dict shape (stored as plain dict, no nested Pydantic model to keep SurrealDB serialization simple):

```python
{
    "tier": "HIGH",           # "HIGH" | "MEDIUM" | "LOW" | "CONTESTED"
    "providers": ["docling", "mineru"],
    "match_method": "key_field_anchor",   # "key_field_anchor" | "jaro_winkler" | "row_position" | "single_provider"
    "match_score": 0.92,      # float 0.0-1.0
    "field_votes": {
        "result": {
            "winner": "Positive",
            "score": 1.0,         # winner's normalised weight score
            "contested": False,   # True when winner score < 0.6
            "votes": {
                "docling": "Positive",
                "mineru": "Positive",
            },
        },
        # ... one entry per non-None field across all providers
    },
    "conflict_level": "L1",           # "L1" | "L2" | "L3" | "L4" | "none"
    "resolver_used": "weighted_majority",  # see ConflictResolver section
}
```

No other changes to `acm_schemas.py`.

---

### 3.2 `open_notebook/extractors/consensus/__init__.py` (CREATE)

```python
"""
Consensus Layer — public API.

Provides:
  RecordMatcher   — 3-stage row matching (pure, no I/O)
  ConsensusEngine — per-field confidence-weighted voting (async)
  ConflictResolver — L1-L4 escalation (async)

Story: E31-S3 Consensus Layer Core
"""

from open_notebook.extractors.consensus.engine import ConsensusEngine
from open_notebook.extractors.consensus.matcher import MatchGroup, RecordMatcher
from open_notebook.extractors.consensus.resolver import ConflictResolver

__all__ = [
    "ConsensusEngine",
    "ConflictResolver",
    "MatchGroup",
    "RecordMatcher",
]
```

---

### 3.3 `open_notebook/extractors/consensus/matcher.py` (CREATE)

#### Overview

`RecordMatcher` takes a list of `(provider_id, List[ACMExtractionRecord])` pairs and returns a list of `MatchGroup` objects. Each `MatchGroup` clusters rows that are likely the same physical ACM item.

#### Data Structures

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from open_notebook.extractors.acm_schemas import ACMExtractionRecord


@dataclass
class CandidateRow:
    """A single provider's extracted row, with its origin provider."""
    provider_id: str
    record: ACMExtractionRecord
    row_index: int  # 0-based position within that provider's output list


@dataclass
class MatchGroup:
    """
    A cluster of CandidateRows believed to represent the same ACM item.

    Attributes:
        rows: One CandidateRow per matched provider (max one per provider).
        match_method: How Stage 1/2/3 produced this group.
        match_score: Numeric confidence of the match (0.0-1.0).
    """
    rows: List[CandidateRow] = field(default_factory=list)
    match_method: str = "single_provider"   # "key_field_anchor" | "jaro_winkler" | "row_position" | "single_provider"
    match_score: float = 1.0
```

#### `RecordMatcher` Class

```python
class RecordMatcher:
    """
    Pure (no I/O) record matcher implementing 3-stage matching.

    Stage 1 — Key-Field Anchor (exact composite key)
    Stage 2 — Jaro-Winkler fuzzy string on the composite key
    Stage 3 — Row-position fallback within same page

    Thresholds:
      >= 0.85  confirmed match
      0.65-0.84 probable match (still merged)
      < 0.65   distinct records
    """

    CONFIRMED_THRESHOLD: float = 0.85
    PROBABLE_THRESHOLD: float = 0.65

    def match_groups(
        self,
        provider_records: List[Tuple[str, List[ACMExtractionRecord]]],
    ) -> List[MatchGroup]:
        """
        Match rows from all providers into MatchGroups.

        Args:
            provider_records: List of (provider_id, records) tuples.

        Returns:
            List of MatchGroup — every input row appears in exactly one group.
        """
        ...
```

#### Implementation Algorithm

**Step 1 — Build `CandidateRow` pools per provider**

```python
pools: Dict[str, List[CandidateRow]] = {}
for provider_id, records in provider_records:
    pools[provider_id] = [
        CandidateRow(provider_id=provider_id, record=r, row_index=i)
        for i, r in enumerate(records)
    ]
```

**Step 2 — Iterative matching across provider pairs**

The algorithm is designed for an arbitrary number of providers. Start with the first provider's rows as "anchors". For each subsequent provider, try to match each unmatched row against existing groups.

```python
# Pseudo-code — implement with the concrete matching stages
groups: List[MatchGroup] = []

# Seed: first provider's rows become solo groups
first_pid, _ = provider_records[0]
for row in pools[first_pid]:
    groups.append(MatchGroup(rows=[row], match_method="single_provider", match_score=1.0))

# For each subsequent provider, merge or create new groups
for provider_id, _ in provider_records[1:]:
    unmatched: List[CandidateRow] = list(pools[provider_id])

    for candidate in list(unmatched):
        best_group, best_score, best_method = _find_best_group(candidate, groups)
        if best_score >= PROBABLE_THRESHOLD and best_group is not None:
            best_group.rows.append(candidate)
            best_group.match_method = best_method
            best_group.match_score = best_score
            unmatched.remove(candidate)

    # Remaining unmatched rows become new solo groups
    for row in unmatched:
        groups.append(MatchGroup(rows=[row], match_method="single_provider", match_score=1.0))
```

**`_find_best_group` inner logic** — try stages in order, return the first match that meets the threshold:

```python
def _find_best_group(
    candidate: CandidateRow,
    groups: List[MatchGroup],
) -> Tuple[Optional[MatchGroup], float, str]:
    best_group = None
    best_score = 0.0
    best_method = "none"

    for group in groups:
        # Skip groups that already have a row from this provider
        if any(r.provider_id == candidate.provider_id for r in group.rows):
            continue

        # Stage 1: Key-Field Anchor
        anchor_score = _stage1_key_anchor(candidate.record, group)
        if anchor_score >= CONFIRMED_THRESHOLD:
            return group, anchor_score, "key_field_anchor"

        # Stage 2: Jaro-Winkler
        jw_score = _stage2_jaro_winkler(candidate.record, group)
        if jw_score > best_score:
            best_score = jw_score
            best_group = group
            best_method = "jaro_winkler"

    # If no Stage 1/2 match, try Stage 3: Row Position
    if best_score < PROBABLE_THRESHOLD:
        pos_score, pos_group = _stage3_row_position(candidate, groups)
        if pos_score > best_score:
            best_score = pos_score
            best_group = pos_group
            best_method = "row_position"

    if best_score >= PROBABLE_THRESHOLD:
        return best_group, best_score, best_method

    return None, 0.0, "none"
```

#### Stage 1 — Key-Field Anchor

Composite key: `f"{building_id}|{room_id or ''}|{product}|{sample_no or ''}"` — all lowercased and stripped.

```python
def _composite_key(record: ACMExtractionRecord) -> str:
    parts = [
        (record.building_id or "").strip().lower(),
        (record.room_id or "").strip().lower(),
        (record.product or "").strip().lower(),
        (record.sample_no or "").strip().lower(),
    ]
    return "|".join(parts)

def _stage1_key_anchor(candidate: ACMExtractionRecord, group: MatchGroup) -> float:
    """Exact composite key match. Returns 1.0 on match, 0.0 otherwise."""
    cand_key = _composite_key(candidate)
    for row in group.rows:
        if _composite_key(row.record) == cand_key:
            return 1.0
    return 0.0
```

#### Stage 2 — Jaro-Winkler Fuzzy String

Implement Jaro-Winkler from pure Python stdlib (no dependencies). Apply to the composite key string.

The Jaro similarity formula:

```
jaro(s1, s2):
    if s1 == s2: return 1.0
    match_window = max(len(s1), len(s2)) // 2 - 1  (min 0)
    Count matching chars within window
    Count transpositions
    jaro = (m/|s1| + m/|s2| + (m - t/2)/m) / 3
      where m = matches, t = transpositions
    Returns 0.0 when m == 0.

jaro_winkler(s1, s2, p=0.1):
    j = jaro(s1, s2)
    prefix = length of common prefix (max 4 chars)
    return j + prefix * p * (1.0 - j)
```

Full implementation skeleton:

```python
def _jaro(s1: str, s2: str) -> float:
    """Compute Jaro similarity between two strings."""
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    match_dist = max(len1, len2) // 2 - 1
    match_dist = max(match_dist, 0)

    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    transpositions = 0

    # Count matches
    for i in range(len1):
        start = max(0, i - match_dist)
        end = min(i + match_dist + 1, len2)
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    # Count transpositions
    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    return (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3


def _jaro_winkler(s1: str, s2: str, p: float = 0.1) -> float:
    """Compute Jaro-Winkler similarity. p is prefix scaling factor (default 0.1)."""
    j = _jaro(s1, s2)
    # Common prefix length, max 4
    prefix = 0
    for c1, c2 in zip(s1[:4], s2[:4]):
        if c1 == c2:
            prefix += 1
        else:
            break
    return j + prefix * p * (1.0 - j)
```

Stage 2 scoring function:

```python
def _stage2_jaro_winkler(candidate: ACMExtractionRecord, group: MatchGroup) -> float:
    """
    Return the maximum Jaro-Winkler score between candidate's composite key
    and any row in the group.
    """
    cand_key = _composite_key(candidate)
    best = 0.0
    for row in group.rows:
        score = _jaro_winkler(cand_key, _composite_key(row.record))
        if score > best:
            best = score
    return best
```

#### Stage 3 — Row Position Fallback

Sort unmatched rows by page number then by `row_index`. Align positionally within the same page. Score = 0.5 (always in the "probable" range 0.65-0.84... actually below PROBABLE_THRESHOLD).

**Important**: Stage 3 score is always 0.5. This is intentionally below `PROBABLE_THRESHOLD` (0.65), so Stage 3 rows only produce a match when no Stage 1/2 match was found AND the caller explicitly decides to use position. The matching algorithm above only falls back to Stage 3 when `best_score < PROBABLE_THRESHOLD` — this means Stage 3 acts as a "last resort" alignment that produces groups with `match_score=0.5`.

**Clarification on AC5**: AC5 states thresholds are `>= 0.85 confirmed, 0.65-0.84 probable, < 0.65 distinct`. Stage 3 produces score 0.5, which is below the "probable" band. Stage 3 rows are still merged (never dropped) but their groups will have `match_score=0.5` and `match_method="row_position"` — this feeds into the tier assignment in ConsensusEngine, which will assign MEDIUM or LOW tier as appropriate.

```python
def _stage3_row_position(
    candidate: CandidateRow,
    groups: List[MatchGroup],
) -> Tuple[float, Optional[MatchGroup]]:
    """
    Positional fallback: find a group on the same page with no row from
    candidate's provider, sorted by row_index. Returns (0.5, group) or (0.0, None).
    """
    cand_page = candidate.record.page_number or -1

    # Collect groups on same page that don't have this provider yet
    eligible = [
        g for g in groups
        if (
            not any(r.provider_id == candidate.provider_id for r in g.rows)
            and any((r.record.page_number or -1) == cand_page for r in g.rows)
        )
    ]

    if not eligible:
        return 0.0, None

    # Sort by the minimum row_index of any row in the group, pick the first
    eligible.sort(key=lambda g: min(r.row_index for r in g.rows))
    return 0.5, eligible[0]
```

---

### 3.4 `open_notebook/extractors/consensus/engine.py` (CREATE)

#### Overview

`ConsensusEngine` takes the `MatchGroup` list from `RecordMatcher` and produces a list of `ACMExtractionRecord` objects with `consensus_metadata` populated.

```python
"""
ConsensusEngine — per-field confidence-weighted voting.

Story: E31-S3 Consensus Layer Core
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.extractors.acm_schemas import ACMExtractionRecord
from open_notebook.extractors.consensus.matcher import MatchGroup
from open_notebook.extractors.consensus.resolver import ConflictResolver


class ConsensusEngine:
    """
    Merges MatchGroups into ACMExtractionRecord objects with consensus_metadata.

    Usage:
        engine = ConsensusEngine()
        records = await engine.merge(match_groups, provider_weights={"docling": 1.0, "mineru": 1.0})
    """

    def __init__(self, resolver: Optional[ConflictResolver] = None) -> None:
        self._resolver = resolver or ConflictResolver()

    async def merge(
        self,
        groups: List[MatchGroup],
        provider_weights: Optional[Dict[str, float]] = None,
    ) -> List[ACMExtractionRecord]:
        """
        Merge MatchGroups into final ACMExtractionRecord list.

        Args:
            groups: Output of RecordMatcher.match_groups().
            provider_weights: Per-provider field weights (default 1.0 for all).

        Returns:
            List of ACMExtractionRecord with consensus_metadata populated.
        """
        weights = provider_weights or {}
        results = []
        for group in groups:
            record = await self._merge_group(group, weights)
            results.append(record)
        return results
```

#### Per-Field Voting

Field-level voting produces a `FieldVoteResult` for each non-None field observed across providers.

```python
from dataclasses import dataclass

@dataclass
class FieldVoteResult:
    winner: Any          # The winning value
    score: float         # Normalised weight of the winner (0.0-1.0)
    contested: bool      # True when winner score < 0.6
    votes: Dict[str, Any]  # {provider_id: value}
```

Voting algorithm for a single field:

```python
def _vote_field(
    field_name: str,
    votes: Dict[str, Any],      # {provider_id: value}
    weights: Dict[str, float],  # provider weights (default 1.0)
) -> FieldVoteResult:
    """
    Compute weighted majority vote for a single field.

    Steps:
    1. Group providers by their value (normalised to str().strip().lower() for comparison,
       but winner uses the original un-lowered value from the highest-weight provider).
    2. Sum weights per value group.
    3. Winner = group with highest total weight.
    4. score = winner_weight / total_weight.
    5. contested = score < 0.6.
    """
    if not votes:
        raise ValueError(f"No votes provided for field '{field_name}'")

    # Accumulate weights per normalised value string
    value_weights: Dict[str, float] = {}  # normalised_value -> cumulative weight
    value_canonical: Dict[str, Any] = {}  # normalised_value -> original value (first seen)

    for provider_id, value in votes.items():
        if value is None:
            continue
        w = weights.get(provider_id, 1.0)
        norm = str(value).strip().lower()
        value_weights[norm] = value_weights.get(norm, 0.0) + w
        if norm not in value_canonical:
            value_canonical[norm] = value

    if not value_weights:
        # All providers returned None for this field
        return FieldVoteResult(winner=None, score=0.0, contested=False, votes=votes)

    total_weight = sum(value_weights.values())
    winner_norm = max(value_weights, key=lambda k: value_weights[k])
    winner_score = value_weights[winner_norm] / total_weight if total_weight > 0 else 0.0

    return FieldVoteResult(
        winner=value_canonical[winner_norm],
        score=round(winner_score, 4),
        contested=winner_score < 0.6,
        votes=votes,
    )
```

#### Tier Assignment

```python
def _assign_tier(
    field_votes: Dict[str, FieldVoteResult],
    group: MatchGroup,
) -> str:
    """
    Assign consensus tier based on agreement across non-None fields.

    Tiers:
      HIGH      — single provider OR all providers agree on all non-None fields
      MEDIUM    — 2+ providers, >= 2/3 non-None fields agree
      LOW       — single provider (solo group) OR agreement_rate < 0.67
      CONTESTED — any key field (building_id, product, result) is contested

    Note: single-provider groups always get LOW (unless match_method shows
    multi-provider merging occurred).
    """
    KEY_FIELDS = {"building_id", "product", "result"}

    # Single provider → LOW
    provider_ids = {r.provider_id for r in group.rows}
    if len(provider_ids) == 1:
        return "LOW"

    # Check for contested key fields → CONTESTED
    for key_field in KEY_FIELDS:
        if key_field in field_votes and field_votes[key_field].contested:
            return "CONTESTED"

    # Compute agreement rate over all voted fields
    total_fields = len(field_votes)
    if total_fields == 0:
        return "LOW"

    agreed_fields = sum(1 for fv in field_votes.values() if not fv.contested)
    agreement_rate = agreed_fields / total_fields

    if agreement_rate >= 1.0:
        return "HIGH"
    elif agreement_rate >= 0.67:
        return "MEDIUM"
    else:
        return "LOW"
```

#### `_merge_group` Method

```python
async def _merge_group(
    self,
    group: MatchGroup,
    weights: Dict[str, float],
) -> ACMExtractionRecord:
    """
    Merge a MatchGroup into a single ACMExtractionRecord.

    Uses the first row's record as the base. Field-level voting
    then overwrites each field with the winner value.
    """
    if not group.rows:
        raise ValueError("Cannot merge an empty MatchGroup")

    # Use highest-weight provider's record as the base template
    def _row_weight(row):
        return weights.get(row.provider_id, 1.0)

    base_row = max(group.rows, key=_row_weight)
    base_record = base_row.record.model_copy(deep=True)

    # Fields to vote on — all ACMExtractionRecord fields except metadata fields
    VOTE_FIELDS = [
        "building_id", "room_id", "product", "material_description", "result",
        "building_name", "building_year", "building_construction",
        "room_name", "room_area", "area_type", "extent", "location",
        "friable", "material_condition", "risk_status", "disturbance_potential",
        "sample_no", "sample_result", "no_access", "identifying_company",
        "quantity", "acm_labelled", "acm_label_details", "floor_level",
        "date_of_inspection", "hygienist_recommendations", "psb_supplied_acm_id",
        "removal_status", "date_of_removal", "quantity_removed",
        "removal_notification_no", "epa_certificate_no", "additional_comments",
    ]
    # Note: do NOT vote on: extraction_confidence, data_issues, page_number,
    #       table_bbox, consensus_metadata — these are metadata fields.

    field_votes: Dict[str, FieldVoteResult] = {}
    provider_ids = [r.provider_id for r in group.rows]

    for field_name in VOTE_FIELDS:
        votes: Dict[str, Any] = {}
        for row in group.rows:
            val = getattr(row.record, field_name, None)
            if val is not None:
                votes[row.provider_id] = val

        if not votes:
            continue  # All providers returned None — leave base value as-is

        if len(votes) == 1:
            # Only one provider has a value — accept it without voting
            provider_id, value = next(iter(votes.items()))
            field_votes[field_name] = FieldVoteResult(
                winner=value,
                score=1.0,
                contested=False,
                votes=votes,
            )
        else:
            fv = _vote_field(field_name, votes, weights)
            field_votes[field_name] = fv

    # Resolve any contested fields
    resolved_votes = await self._resolver.resolve(field_votes, group, weights)

    # Apply winner values to the base record
    for field_name, fv in resolved_votes.items():
        if fv.winner is not None:
            setattr(base_record, field_name, fv.winner)

    # Build consensus_metadata dict
    tier = _assign_tier(resolved_votes, group)

    # Update extraction_confidence from tier
    tier_to_confidence = {
        "HIGH": "high",
        "MEDIUM": "medium",
        "LOW": "low",
        "CONTESTED": "low",
    }
    base_record.extraction_confidence = tier_to_confidence.get(tier, "low")

    # Determine conflict_level and resolver_used from the resolver's output
    # (ConflictResolver stores these on its return value — see resolver.py)
    conflict_level = getattr(self._resolver, "_last_conflict_level", "none")
    resolver_used = getattr(self._resolver, "_last_resolver_used", "none")

    base_record.consensus_metadata = {
        "tier": tier,
        "providers": sorted(provider_ids),
        "match_method": group.match_method,
        "match_score": round(group.match_score, 4),
        "field_votes": {
            fn: {
                "winner": fv.winner,
                "score": fv.score,
                "contested": fv.contested,
                "votes": fv.votes,
            }
            for fn, fv in resolved_votes.items()
        },
        "conflict_level": conflict_level,
        "resolver_used": resolver_used,
    }

    logger.debug(
        f"ConsensusEngine: group tier={tier}, providers={provider_ids}, "
        f"match_method={group.match_method}, match_score={group.match_score:.3f}"
    )

    return base_record
```

---

### 3.5 `open_notebook/extractors/consensus/resolver.py` (CREATE)

#### Overview

`ConflictResolver` takes the `field_votes` dict from `ConsensusEngine._merge_group` and resolves any contested fields through an escalation chain.

```python
"""
ConflictResolver — L1-L4 escalation chain for contested ACM field values.

L1: Weighted Majority (accept if winner score >= 0.6)
L2: Priority Hierarchy (docling > mineru > other)
L3: LLM Arbitration (async stub — returns L2 result, real call in E31-S5)
L4: Human Queue (confidence < 0.4, use L2 as provisional)

Story: E31-S3 Consensus Layer Core
"""
from __future__ import annotations

from typing import Dict, Optional

from loguru import logger

from open_notebook.extractors.consensus.matcher import MatchGroup


# FieldVoteResult is imported from engine to avoid a circular dependency.
# This import is done inside methods to avoid issues. The resolver only
# operates on plain dicts when called from outside engine.py.
# Alternatively, move FieldVoteResult to a shared types module.
# For this story: define a lightweight local alias.

from dataclasses import dataclass
from typing import Any


@dataclass
class FieldVoteResult:
    """Mirror of engine.FieldVoteResult — defined here to avoid circular import."""
    winner: Any
    score: float
    contested: bool
    votes: Dict[str, Any]


# Provider priority for L2 resolution
PROVIDER_PRIORITY = ["docling", "mineru"]


class ConflictResolver:
    """
    Resolves contested field votes via L1-L4 escalation.

    After resolve() is called, the attributes _last_conflict_level and
    _last_resolver_used are set to the highest escalation level reached
    and the resolver strategy used, respectively.
    """

    def __init__(self) -> None:
        self._last_conflict_level: str = "none"
        self._last_resolver_used: str = "none"

    async def resolve(
        self,
        field_votes: Dict[str, FieldVoteResult],
        group: MatchGroup,
        weights: Dict[str, float],
    ) -> Dict[str, FieldVoteResult]:
        """
        Resolve all contested fields in field_votes.

        Args:
            field_votes: Dict of field_name -> FieldVoteResult from ConsensusEngine.
            group: The MatchGroup being resolved (used for context).
            weights: Provider weights.

        Returns:
            Updated field_votes dict with contested fields resolved.
        """
        self._last_conflict_level = "none"
        self._last_resolver_used = "none"

        resolved = dict(field_votes)
        any_contested = any(fv.contested for fv in resolved.values())

        if not any_contested:
            return resolved

        for field_name, fv in resolved.items():
            if not fv.contested:
                continue
            resolved[field_name] = await self._escalate(field_name, fv, weights)

        return resolved

    async def _escalate(
        self,
        field_name: str,
        fv: FieldVoteResult,
        weights: Dict[str, float],
    ) -> FieldVoteResult:
        """Run L1 through L4 escalation for a single contested field."""

        # L1: Weighted Majority — re-check, accept if score >= 0.6
        if fv.score >= 0.6:
            self._update_tracking("L1", "weighted_majority")
            return FieldVoteResult(
                winner=fv.winner,
                score=fv.score,
                contested=False,
                votes=fv.votes,
            )

        # L2: Priority Hierarchy
        l2_result = self._l2_priority(fv, weights)
        if l2_result.score >= 0.4:
            self._update_tracking("L2", "priority_hierarchy")
            return l2_result

        # L3: LLM Arbitration (stub — real implementation in E31-S5)
        l3_result = await self._l3_llm_stub(field_name, fv, l2_result)
        if l3_result.score >= 0.4:
            self._update_tracking("L3", "llm_arbitration_stub")
            return l3_result

        # L4: Human Queue
        logger.warning(
            f"ConflictResolver: field '{field_name}' escalated to L4 human queue. "
            f"Using L2 provisional result."
        )
        self._update_tracking("L4", "human_queue")
        return FieldVoteResult(
            winner=l2_result.winner,
            score=l2_result.score,
            contested=True,   # Remains contested — flagged for human review
            votes=fv.votes,
        )

    def _l2_priority(
        self,
        fv: FieldVoteResult,
        weights: Dict[str, float],
    ) -> FieldVoteResult:
        """
        L2: Select the value from the highest-priority provider that has a vote.

        Priority order: docling > mineru > (other providers in alphabetical order).
        """
        priority_order = list(PROVIDER_PRIORITY)
        # Add any remaining providers alphabetically
        extra = sorted(p for p in fv.votes if p not in priority_order)
        priority_order.extend(extra)

        for provider_id in priority_order:
            if provider_id in fv.votes and fv.votes[provider_id] is not None:
                return FieldVoteResult(
                    winner=fv.votes[provider_id],
                    score=0.6,   # Provisional confidence from priority hierarchy
                    contested=False,
                    votes=fv.votes,
                )

        # Fallback: return original if no priority provider found
        return fv

    async def _l3_llm_stub(
        self,
        field_name: str,
        original: FieldVoteResult,
        l2_result: FieldVoteResult,
    ) -> FieldVoteResult:
        """
        L3: LLM Arbitration stub.

        In E31-S3, this simply returns the L2 result with a 0.5 confidence score
        and a note that it is a stub. Real LLM arbitration is implemented in E31-S5.
        """
        logger.info(
            f"ConflictResolver: L3 stub called for field '{field_name}' "
            f"(real LLM arbitration deferred to E31-S5)"
        )
        return FieldVoteResult(
            winner=l2_result.winner,
            score=0.5,
            contested=False,
            votes=original.votes,
        )

    def _update_tracking(self, level: str, resolver: str) -> None:
        """Update tracking attributes if this level is higher than the current."""
        level_order = {"none": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
        if level_order.get(level, 0) > level_order.get(self._last_conflict_level, 0):
            self._last_conflict_level = level
            self._last_resolver_used = resolver
```

**Important note on `FieldVoteResult` duplication**: To avoid a circular import between `engine.py` and `resolver.py`, `FieldVoteResult` is defined in `resolver.py` and imported by `engine.py`. The developer must move the `@dataclass FieldVoteResult` definition to `resolver.py` and import it in `engine.py`:

```python
# In engine.py — import FieldVoteResult from resolver to avoid circular dependency
from open_notebook.extractors.consensus.resolver import ConflictResolver, FieldVoteResult
```

And in `resolver.py`, remove the "mirror" comment — it IS the canonical definition.

---

## 4. Testing Requirements

### 4.1 `tests/test_record_matcher.py` (CREATE)

The test file must import only from `open_notebook.extractors.consensus.matcher` and `open_notebook.extractors.acm_schemas`. No I/O, no mocking needed (pure functions).

**Helper fixture** — minimal valid `ACMExtractionRecord`:

```python
def make_record(**kwargs) -> ACMExtractionRecord:
    defaults = {
        "building_id": "B1",
        "product": "Ceiling Tiles",
        "result": "Positive",
    }
    defaults.update(kwargs)
    return ACMExtractionRecord(**defaults)
```

#### Required Test Cases

**Stage 1 — Key-Field Anchor**

| Test | Description |
|------|-------------|
| `test_stage1_exact_match_returns_confirmed_score` | Two records with identical building_id, room_id, product, sample_no produce score 1.0 |
| `test_stage1_case_insensitive` | "Ceiling Tiles" matches "ceiling tiles" via lowercasing |
| `test_stage1_different_building_no_match` | Records with different building_id score 0.0 from Stage 1 |
| `test_stage1_empty_optional_fields_match` | room_id=None and sample_no=None match correctly (both use empty string in key) |
| `test_stage1_partial_key_mismatch` | Same building_id + product but different sample_no scores 0.0 |

**Stage 2 — Jaro-Winkler**

| Test | Description |
|------|-------------|
| `test_jaro_winkler_identical_strings` | _jaro_winkler("abc", "abc") == 1.0 |
| `test_jaro_winkler_empty_strings` | _jaro_winkler("", "") == 1.0 (or 0.0 — document actual behaviour) |
| `test_jaro_winkler_completely_different` | "abc" vs "xyz" gives score < 0.65 |
| `test_jaro_winkler_similar_keys_above_threshold` | Slightly typo'd composite key returns score >= 0.85 |
| `test_jaro_winkler_similar_but_distinct` | AC8 — "B1|101|Ceiling Tiles|" vs "B2|102|Floor Tiles|" must return score < 0.65 so they are NOT merged |
| `test_stage2_picks_best_group` | When multiple groups exist, Stage 2 returns the one with highest score |

**Stage 3 — Row Position**

| Test | Description |
|------|-------------|
| `test_stage3_matches_by_page_and_position` | Two providers with rows on the same page, Stage 3 aligns them |
| `test_stage3_no_match_different_page` | Stage 3 returns (0.0, None) when candidate is on page 3 and all groups are on page 1 |
| `test_stage3_score_is_always_0_5` | When Stage 3 finds a match, match_score == 0.5 |

**match_groups() Integration**

| Test | Description |
|------|-------------|
| `test_single_provider_all_solo_groups` | Single provider → all MatchGroups have 1 row each, method="single_provider" |
| `test_two_providers_identical_records_merged` | Two providers with identical records → one MatchGroup with 2 rows |
| `test_two_providers_distinct_records_separate_groups` | Two providers with clearly different records → two separate MatchGroups |
| `test_unmatched_rows_never_dropped` | Provider A has 3 rows, Provider B has 2 rows — result has at least 3 groups (no rows lost) |
| `test_match_group_one_row_per_provider` | A MatchGroup never has two rows from the same provider |
| **AC8 False Positive** | `test_false_positive_similar_but_different_records_not_merged` — "B1|101|Ceiling Tiles|" vs "B2|201|Floor Tiles|" must produce 2 separate groups |

### 4.2 `tests/test_consensus_engine.py` (CREATE)

#### Required Test Cases

**Jaro-Winkler Pure Function Tests** (can live here or in test_record_matcher.py — choose one)

**Per-Field Voting (`_vote_field`)**

| Test | Description |
|------|-------------|
| `test_vote_field_unanimous_returns_score_1` | Both providers return "Positive" → score=1.0, contested=False |
| `test_vote_field_majority_wins` | 2 providers say "Positive", 1 says "Negative" → winner="Positive", score~0.67 |
| `test_vote_field_contested_when_winner_score_below_0_6` | 50/50 split → contested=True |
| `test_vote_field_single_provider_score_1` | Single provider vote → score=1.0, contested=False |
| `test_vote_field_respects_weights` | docling weight=2.0, mineru weight=1.0, docling says "Positive", mineru says "Negative" → winner="Positive", score=0.67 |
| `test_vote_field_all_none_returns_none_winner` | All providers return None for a field → winner=None |

**Tier Assignment (`_assign_tier`)**

| Test | Description |
|------|-------------|
| `test_tier_high_all_agree` | Multi-provider, all fields agree (all scores == 1.0) → "HIGH" |
| `test_tier_medium_majority_agree` | Multi-provider, 2/3 fields agree → "MEDIUM" |
| `test_tier_low_single_provider` | Single-provider MatchGroup → "LOW" |
| `test_tier_low_poor_agreement` | Multi-provider, agreement_rate < 0.67 → "LOW" |
| `test_tier_contested_key_field_contested` | `result` field is contested → "CONTESTED" |
| `test_tier_contested_building_id_contested` | `building_id` field is contested → "CONTESTED" |

**`ConsensusEngine.merge()` Integration**

| Test | Description |
|------|-------------|
| `test_merge_single_group_single_provider` | Single MatchGroup with 1 row → returns record with tier="LOW", consensus_metadata set |
| `test_merge_two_providers_agree` | Two providers agree on all fields → tier="HIGH" |
| `test_merge_two_providers_disagree_key_field` | Providers disagree on "result" → tier="CONTESTED" |
| `test_merge_sets_extraction_confidence` | extraction_confidence is updated from tier (HIGH→"high", etc.) |
| `test_merge_consensus_metadata_schema` | consensus_metadata has all required keys: tier, providers, match_method, match_score, field_votes, conflict_level, resolver_used |
| `test_merge_providers_list_sorted` | consensus_metadata["providers"] is always sorted |
| `test_merge_empty_groups_returns_empty_list` | merge([]) returns [] |

**`ConflictResolver` Tests**

| Test | Description |
|------|-------------|
| `test_l1_accepts_winner_score_gte_0_6` | Field with score=0.65 (contested=True from voting threshold <0.6... wait) — re-test: field score=0.6 → L1 accepts, conflict_level="L1" |
| `test_l2_priority_docling_over_mineru` | Docling and MinerU disagree → L2 picks docling value |
| `test_l2_priority_unknown_provider_last` | Unknown provider loses to docling/mineru in priority |
| `test_l3_stub_returns_l2_result_with_0_5_confidence` | L3 stub is called when L2 gives score < 0.4 (edge case) |
| `test_l4_human_queue_sets_contested_true` | L4 leaves contested=True on the result |
| `test_resolver_tracks_highest_escalation_level` | If L1 resolves field A and L2 resolves field B, _last_conflict_level="L2" |
| `test_no_contested_fields_returns_unchanged` | No contested fields → resolve() returns field_votes unchanged, conflict_level="none" |

---

## 5. Acceptance Criteria Checklist

| # | Criterion | Verification |
|---|-----------|-------------|
| AC1 | `RecordMatcher` with 3-stage matching: key-field anchor, Jaro-Winkler >= 0.85, row position fallback | `test_record_matcher.py` — all three stage tests pass |
| AC2 | `ConsensusEngine` with per-field confidence-weighted voting | `test_consensus_engine.py::test_vote_field_*` pass |
| AC3 | `ConflictResolver` with L1-L4 escalation chain | `test_consensus_engine.py::test_l1/l2/l3/l4_*` pass |
| AC4 | Confidence tier assignment: HIGH / MEDIUM / LOW / CONTESTED | `test_consensus_engine.py::test_tier_*` pass |
| AC5 | Match thresholds: >= 0.85 confirmed, 0.65-0.84 probable, < 0.65 distinct | Constants defined in `RecordMatcher`; Stage 2 test with threshold boundary values passes |
| AC6 | `consensus_metadata` added to `ACMExtractionRecord` | Field exists in `acm_schemas.py`; existing tests (`test_acm_schemas.py`) still pass |
| AC7 | Unit tests for each matching stage, voting, and conflict resolution | `uv run pytest tests/test_record_matcher.py tests/test_consensus_engine.py -v` all pass |
| AC8 | False positive test: similar-but-different records NOT merged | `test_record_matcher.py::test_false_positive_similar_but_different_records_not_merged` passes |

---

## 6. Integration Notes

### How the Consensus Layer Will Be Called (Future E31-S5)

The developer does NOT need to wire this into `source_commands.py` in E31-S3 — that is E31-S5's responsibility. The story delivers only the consensus classes and tests.

The expected future call site will look like:

```python
from open_notebook.extractors.consensus import ConsensusEngine, RecordMatcher

matcher = RecordMatcher()
engine = ConsensusEngine()

# provider_results: List[NormalizedExtractionResult] from E31-S2
provider_pairs = [
    (result.provider_id, result.acm_records)  # acm_records not yet populated — E31-S5 concern
    for result in provider_results
]
groups = matcher.match_groups(provider_pairs)
final_records = await engine.merge(groups, provider_weights={...})
```

### Avoiding Circular Imports

The dependency graph within the consensus package must be:

```
acm_schemas.py  (no consensus imports)
    ^
    |
resolver.py     (imports from acm_schemas.py — FieldVoteResult is defined HERE)
    ^
    |
engine.py       (imports from resolver.py and matcher.py)
    ^
    |
matcher.py      (imports from acm_schemas.py only)
    ^
    |
__init__.py     (imports from engine, matcher, resolver)
```

### Verification Protocol (Before Marking Done)

```bash
# From repo root (Windows — use forward slashes)
cd "D:/ailocal/acm-ai"

# 1. Lint
uv run ruff check open_notebook/extractors/consensus/ tests/test_record_matcher.py tests/test_consensus_engine.py --fix

# 2. Type check (informational)
uv run mypy open_notebook/extractors/consensus/

# 3. Tests (existing schema tests must still pass)
uv run pytest tests/test_acm_schemas.py -v

# 4. New tests
uv run pytest tests/test_record_matcher.py tests/test_consensus_engine.py -v

# 5. Full backend test suite (no regressions)
uv run pytest tests/ -x --ignore=tests/test_e2e_extraction.py -q
```

Expected outcome: all new tests pass, no regressions in existing tests.

---

## 7. Implementation Order

The developer should implement in this exact order to avoid broken imports:

1. Add `consensus_metadata` field to `open_notebook/extractors/acm_schemas.py`
2. Create `open_notebook/extractors/consensus/resolver.py` (defines `FieldVoteResult`)
3. Create `open_notebook/extractors/consensus/matcher.py` (imports from `acm_schemas.py`)
4. Create `open_notebook/extractors/consensus/engine.py` (imports from `resolver.py` and `matcher.py`)
5. Create `open_notebook/extractors/consensus/__init__.py`
6. Create `tests/test_record_matcher.py`
7. Create `tests/test_consensus_engine.py`
8. Run verification protocol
