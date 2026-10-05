"""Ties filters + scoring together: ARCHITECTURE.md > Matching, display rules."""
from __future__ import annotations

from collections.abc import Iterable

from .filters import apply_hard_filters
from .scoring import score_listing
from .types import Listing, MatchRunResult, Profile, SearchContext

MAX_RESULTS = 5


def run_match(profile: Profile, context: SearchContext, listings: Iterable[Listing]) -> MatchRunResult:
    passing, excluded, other_path_count = apply_hard_filters(profile, context, listings)

    scored = [score_listing(profile, context, listing) for listing in passing]
    displayable = [r for r in scored if r.label is not None]
    # Tie-break: score desc, then listing ID asc (ARCHITECTURE.md > Matching > Score).
    displayable.sort(key=lambda r: (-r.score, r.job_id))

    top = displayable[:MAX_RESULTS]
    for rank, result in enumerate(top, start=1):
        result.rank = rank

    return MatchRunResult(results=top, excluded=excluded, other_path_count=other_path_count)
