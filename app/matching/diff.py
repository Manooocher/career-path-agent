"""ARCHITECTURE.md > Matching > Diff (for "what changed").

Compares a run's displayed+excluded results with its parent run's displayed
results: listings that left (with exclusion reason), joined, and moved rank.
Pure function; feedback_effects (the "old -> new" field changes themselves)
are tracked separately by the feedback graph (T-401), not here.
"""
from __future__ import annotations

from typing import Dict, List, TypedDict

from .types import ExcludedResult, MatchResult


class LeftEntry(TypedDict):
    job_id: str
    old_rank: int
    reason_fa: str


class JoinedEntry(TypedDict):
    job_id: str
    new_rank: int


class MovedEntry(TypedDict):
    job_id: str
    old_rank: int
    new_rank: int


class RunDiff(TypedDict):
    left: List[LeftEntry]
    joined: List[JoinedEntry]
    moved: List[MovedEntry]


def diff_runs(
    parent_results: List[MatchResult],
    new_results: List[MatchResult],
    new_excluded: List[ExcludedResult],
) -> RunDiff:
    parent_by_id: Dict[str, MatchResult] = {r.job_id: r for r in parent_results}
    new_by_id: Dict[str, MatchResult] = {r.job_id: r for r in new_results}
    excluded_by_id: Dict[str, ExcludedResult] = {e.job_id: e for e in new_excluded}

    left: List[LeftEntry] = []
    for job_id, old in parent_by_id.items():
        if job_id in new_by_id:
            continue
        excluded = excluded_by_id.get(job_id)
        reason_fa = excluded.reason_fa if excluded else "دیگر در میان نتایج نیست."
        left.append({"job_id": job_id, "old_rank": old.rank, "reason_fa": reason_fa})

    joined: List[JoinedEntry] = []
    moved: List[MovedEntry] = []
    for job_id, new in new_by_id.items():
        old = parent_by_id.get(job_id)
        if old is None:
            joined.append({"job_id": job_id, "new_rank": new.rank})
        elif old.rank != new.rank:
            moved.append({"job_id": job_id, "old_rank": old.rank, "new_rank": new.rank})

    return {"left": left, "joined": joined, "moved": moved}
