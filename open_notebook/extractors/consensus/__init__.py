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
from open_notebook.extractors.consensus.resolver import (
    ConflictResolver,
    FieldVoteResult,
)

__all__ = [
    "ConsensusEngine",
    "ConflictResolver",
    "FieldVoteResult",
    "MatchGroup",
    "RecordMatcher",
]
