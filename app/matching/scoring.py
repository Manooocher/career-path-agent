"""ARCHITECTURE.md > Matching > Score (0-100, rounded half-up to an integer)."""
from __future__ import annotations

import math
from typing import Optional

from .types import Arrangement, Listing, MatchResult, Profile, SearchContext, seniority_level

STRONG_THRESHOLD = 75
POSSIBLE_THRESHOLD = 50
WEAK_THRESHOLD = 35


def round_half_up(value: float) -> int:
    return math.floor(value + 0.5)


def _seniority_fit(profile: Profile, listing: Listing) -> float:
    diff = seniority_level(listing.seniority) - seniority_level(profile.seniority)
    if diff == 0:
        return 1.0
    if diff == -1:
        return 0.8
    if diff == 1:
        return 0.5
    if diff <= -2:
        return 0.5
    return 0.5  # diff >= 2 is excluded by H3 before scoring runs; kept defined for safety


def _salary_fit(context: SearchContext, listing: Listing) -> float:
    if context.salary_floor_toman is None or listing.salary_min_toman is None:
        return 0.5
    if listing.salary_min_toman >= context.salary_floor_toman:
        return 1.0
    if listing.salary_max_toman is not None and listing.salary_max_toman >= context.salary_floor_toman:
        return 0.6
    return 0.5  # H2 would have excluded this listing before scoring runs


def _arrangement_fit(listing: Listing) -> float:
    return 1.0 if listing.arrangement == Arrangement.REMOTE else 0.6


def score_listing(profile: Profile, context: SearchContext, listing: Listing) -> MatchResult:
    s = profile.confirmed_skills
    r = set(listing.required_skills)
    p = set(listing.preferred_skills)
    e = set(context.emphasis_skills)

    considerations = []

    if r:
        required_ratio = len(s & r) / len(r)
    else:
        required_ratio = 1.0
        considerations.append("نیازمندی‌ها مشخص نشده")

    required_weight = 50
    preferred_component = 0.0
    if p:
        preferred_ratio = len(s & p) / len(p)
        preferred_component = 15 * preferred_ratio
    else:
        required_weight += 15

    emphasis_component = 0.0
    if e:
        emphasis_ratio = len(e & (r | p)) / len(e)
        emphasis_component = 5 * emphasis_ratio
    else:
        required_weight += 5

    required_component = required_weight * required_ratio

    seniority_component = 15 * _seniority_fit(profile, listing)
    salary_component = 10 * _salary_fit(context, listing)
    arrangement_component = 5 * _arrangement_fit(listing)

    if listing.salary_min_toman is None:
        considerations.append("حقوق: نامشخص")

    total = (
        required_component
        + preferred_component
        + emphasis_component
        + seniority_component
        + salary_component
        + arrangement_component
    )
    score = max(0, min(100, round_half_up(total)))

    label: Optional[str]
    if score >= STRONG_THRESHOLD:
        label = "strong"
    elif score >= POSSIBLE_THRESHOLD:
        label = "possible"
    elif score >= WEAK_THRESHOLD:
        label = "weak"
    else:
        label = None  # not displayed

    return MatchResult(
        job_id=listing.id,
        score=score,
        label=label,
        matched=sorted(s & (r | p)),
        gaps_required=sorted(r - s),
        gaps_preferred=sorted(p - s),
        considerations=considerations,
    )
