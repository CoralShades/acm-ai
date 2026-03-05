"""
RecordMatcher — 3-stage row matching for consensus layer.

Stage 1: Key-Field Anchor (exact composite key match)
Stage 2: Jaro-Winkler fuzzy string on the composite key
Stage 3: Row-position fallback within same page

Thresholds:
  >= 0.85  confirmed match
  0.65-0.84 probable match (still merged)
  < 0.65   distinct records (not merged via Stage 1/2)

Stage 3 always produces score=0.5 (below PROBABLE_THRESHOLD). Stage 3 results
bypass the threshold gate and are returned unconditionally when a positional match
is found — row-position matched groups receive a lower confidence tier in ConsensusEngine.

No I/O, no external dependencies — uses only Python stdlib math.

Story: E31-S3 Consensus Layer Core
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from open_notebook.extractors.acm_schemas import ACMExtractionRecord

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CandidateRow:
    """A single provider's extracted row with its origin provider.

    Attributes:
        provider_id: Stable identifier for the extraction provider.
        record: The ACMExtractionRecord extracted by this provider.
        row_index: 0-based position within that provider's output list.
    """

    provider_id: str
    record: ACMExtractionRecord
    row_index: int


@dataclass
class MatchGroup:
    """A cluster of CandidateRows believed to represent the same ACM item.

    Attributes:
        rows: One CandidateRow per matched provider (max one per provider).
        match_method: How Stage 1/2/3 produced this group.
            "key_field_anchor" — exact composite key match (Stage 1)
            "jaro_winkler"     — fuzzy string match (Stage 2)
            "row_position"     — positional alignment fallback (Stage 3)
            "single_provider"  — only one provider contributed
        match_score: Numeric confidence of the match (0.0–1.0).
    """

    rows: List[CandidateRow] = field(default_factory=list)
    match_method: str = "single_provider"
    match_score: float = 1.0


# ---------------------------------------------------------------------------
# Jaro-Winkler implementation (pure stdlib — no external dependencies)
# ---------------------------------------------------------------------------


def _jaro(s1: str, s2: str) -> float:
    """Compute Jaro similarity between two strings.

    Args:
        s1: First string.
        s2: Second string.

    Returns:
        Jaro similarity in [0.0, 1.0].
    """
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

    # Count matches within the match window
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

    # Count transpositions (half the number of matching characters that differ
    # in their position in both strings)
    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    return (
        matches / len1 + matches / len2 + (matches - transpositions / 2) / matches
    ) / 3


def _jaro_winkler(s1: str, s2: str, p: float = 0.1) -> float:
    """Compute Jaro-Winkler similarity between two strings.

    The Winkler modification gives higher scores to strings that share a
    common prefix (up to 4 characters).

    Args:
        s1: First string.
        s2: Second string.
        p: Prefix scaling factor (default 0.1, must be <= 0.25).

    Returns:
        Jaro-Winkler similarity in [0.0, 1.0].
    """
    j = _jaro(s1, s2)
    # Common prefix length, max 4 characters
    prefix = 0
    for c1, c2 in zip(s1[:4], s2[:4]):
        if c1 == c2:
            prefix += 1
        else:
            break
    return j + prefix * p * (1.0 - j)


# ---------------------------------------------------------------------------
# Composite key helpers
# ---------------------------------------------------------------------------


def _composite_key(record: ACMExtractionRecord) -> str:
    """Build a normalised composite key for a record.

    Key format: "{building_id}|{room_id}|{product}|{sample_no}"
    All components are lowercased and stripped. None values become "".

    Args:
        record: The ACMExtractionRecord to key.

    Returns:
        Composite key string.
    """
    parts = [
        (record.building_id or "").strip().lower(),
        (record.room_id or "").strip().lower(),
        (record.product or "").strip().lower(),
        (record.sample_no or "").strip().lower(),
    ]
    return "|".join(parts)


# ---------------------------------------------------------------------------
# Stage helper functions
# ---------------------------------------------------------------------------


def _stage1_key_anchor(candidate: ACMExtractionRecord, group: MatchGroup) -> float:
    """Stage 1: Exact composite key match.

    Returns 1.0 if the candidate's composite key exactly matches any row
    in the group (case-insensitive via lowercasing), else 0.0.

    Args:
        candidate: The ACMExtractionRecord to match.
        group: The MatchGroup to match against.

    Returns:
        1.0 on match, 0.0 otherwise.
    """
    cand_key = _composite_key(candidate)
    for row in group.rows:
        if _composite_key(row.record) == cand_key:
            return 1.0
    return 0.0


def _stage2_jaro_winkler(candidate: ACMExtractionRecord, group: MatchGroup) -> float:
    """Stage 2: Jaro-Winkler fuzzy match on composite key.

    Returns the maximum Jaro-Winkler score between the candidate's composite
    key and any row in the group.

    Args:
        candidate: The ACMExtractionRecord to match.
        group: The MatchGroup to match against.

    Returns:
        Maximum Jaro-Winkler score in [0.0, 1.0].
    """
    cand_key = _composite_key(candidate)
    best = 0.0
    for row in group.rows:
        score = _jaro_winkler(cand_key, _composite_key(row.record))
        if score > best:
            best = score
    return best


def _stage3_row_position(
    candidate: CandidateRow,
    groups: List[MatchGroup],
) -> Tuple[float, Optional[MatchGroup]]:
    """Stage 3: Positional fallback — align by page and row_index.

    Finds the first (lowest row_index) eligible group on the same page that
    does not already contain a row from the candidate's provider.

    Requires a known (positive) page_number on the candidate and on at least
    one row in the eligible group. When page_number is None or zero,
    positional alignment is meaningless and (0.0, None) is returned.

    Args:
        candidate: The CandidateRow to match.
        groups: All current MatchGroups.

    Returns:
        Tuple of (score, group) where score=0.5 on match, or (0.0, None).
    """
    cand_page = candidate.record.page_number
    # Require a known page number — None or 0 means the page is unknown and
    # positional alignment cannot be applied reliably.
    if not cand_page or cand_page < 1:
        return 0.0, None

    # Groups on same known page that don't already have this provider
    eligible = [
        g
        for g in groups
        if (
            not any(r.provider_id == candidate.provider_id for r in g.rows)
            and any(
                r.record.page_number == cand_page
                for r in g.rows
                if r.record.page_number is not None and r.record.page_number >= 1
            )
        )
    ]

    if not eligible:
        return 0.0, None

    # Sort by the minimum row_index of any row in the group; pick the first
    eligible.sort(key=lambda g: min(r.row_index for r in g.rows))
    return 0.5, eligible[0]


def _find_best_group(
    candidate: CandidateRow,
    groups: List[MatchGroup],
    confirmed_threshold: float,
    probable_threshold: float,
) -> Tuple[Optional[MatchGroup], float, str]:
    """Try matching stages in order, returning the best group found.

    Stage 1 (exact key) is tried first. If a confirmed match is found it is
    returned immediately. Otherwise Stage 2 (Jaro-Winkler) is tried across
    all groups to find the best score. If Stage 2 finds nothing above the
    probable threshold, Stage 3 (row position) is used as last resort.

    Args:
        candidate: The CandidateRow to match.
        groups: Current MatchGroups (each may have rows from multiple providers).
        confirmed_threshold: Score >= this triggers an immediate Stage 1 return.
        probable_threshold: Score >= this is considered a probable match.

    Returns:
        Tuple of (best_group, best_score, best_method). Returns
        (None, 0.0, "none") when no match meets the probable threshold.
    """
    best_group: Optional[MatchGroup] = None
    best_score = 0.0
    best_method = "none"

    for group in groups:
        # Skip groups that already have a row from this provider
        if any(r.provider_id == candidate.provider_id for r in group.rows):
            continue

        # Stage 1: Key-Field Anchor
        anchor_score = _stage1_key_anchor(candidate.record, group)
        if anchor_score >= confirmed_threshold:
            return group, anchor_score, "key_field_anchor"

        # Stage 2: Jaro-Winkler
        jw_score = _stage2_jaro_winkler(candidate.record, group)
        if jw_score > best_score:
            best_score = jw_score
            best_group = group
            best_method = "jaro_winkler"

    # Stage 3: Row-position fallback — only if Stage 1/2 found nothing above threshold.
    # Stage 3 always scores 0.5 (below probable_threshold). When Stage 1/2 produced no
    # group above the threshold, Stage 3 returns its match unconditionally — it is a
    # last-resort fallback that bypasses the fuzzy score gate entirely.
    if best_score < probable_threshold:
        pos_score, pos_group = _stage3_row_position(candidate, groups)
        if pos_group is not None:
            # Return Stage 3 match unconditionally regardless of any Stage 2 score.
            return pos_group, pos_score, "row_position"

    if best_score >= probable_threshold:
        return best_group, best_score, best_method

    return None, 0.0, "none"


# ---------------------------------------------------------------------------
# RecordMatcher
# ---------------------------------------------------------------------------


class RecordMatcher:
    """Pure (no I/O) record matcher implementing 3-stage matching.

    Stage 1 — Key-Field Anchor (exact composite key)
    Stage 2 — Jaro-Winkler fuzzy string on the composite key
    Stage 3 — Row-position fallback within same page

    Thresholds:
      >= 0.85  confirmed match (Stage 1/2)
      0.65-0.84 probable match (still merged)
      < 0.65   distinct records (not merged via Stages 1 or 2)

    Stage 3 always scores 0.5, which is below PROBABLE_THRESHOLD. Stage 3
    results bypass the threshold gate (returned unconditionally when a
    positional match exists) and receive LOW or MEDIUM tier in ConsensusEngine.
    """

    CONFIRMED_THRESHOLD: float = 0.85
    PROBABLE_THRESHOLD: float = 0.65

    def match_groups(
        self,
        provider_records: List[Tuple[str, List[ACMExtractionRecord]]],
    ) -> List[MatchGroup]:
        """Match rows from all providers into MatchGroups.

        Every input row appears in exactly one MatchGroup. No rows are dropped.

        Args:
            provider_records: List of (provider_id, records) tuples, one per
                provider. If a single provider is supplied, each record becomes
                a solo MatchGroup with match_method="single_provider".

        Returns:
            List of MatchGroup where every input record appears exactly once.
        """
        if not provider_records:
            return []

        # Build CandidateRow pools per provider
        pools: Dict[str, List[CandidateRow]] = {}
        for provider_id, records in provider_records:
            pools[provider_id] = [
                CandidateRow(
                    provider_id=provider_id,
                    record=r,
                    row_index=i,
                )
                for i, r in enumerate(records)
            ]

        groups: List[MatchGroup] = []

        # Seed: first provider's rows become solo groups
        first_pid = provider_records[0][0]
        for row in pools[first_pid]:
            groups.append(
                MatchGroup(rows=[row], match_method="single_provider", match_score=1.0)
            )

        # For each subsequent provider, merge or create new groups
        for provider_id, _ in provider_records[1:]:
            unmatched: List[CandidateRow] = list(pools[provider_id])

            for candidate in list(unmatched):
                best_group, best_score, best_method = _find_best_group(
                    candidate,
                    groups,
                    self.CONFIRMED_THRESHOLD,
                    self.PROBABLE_THRESHOLD,
                )
                if best_group is not None:
                    best_group.rows.append(candidate)
                    best_group.match_method = best_method
                    best_group.match_score = best_score
                    unmatched.remove(candidate)

            # Remaining unmatched rows become new solo groups
            for row in unmatched:
                groups.append(
                    MatchGroup(
                        rows=[row],
                        match_method="single_provider",
                        match_score=1.0,
                    )
                )

        return groups
