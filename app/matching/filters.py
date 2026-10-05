"""ARCHITECTURE.md > Matching > Hard filters (H0-H6).

H6 (military clearance) is a Could item (ARCHITECTURE Cut list, order 1)
and is not implemented here.
"""
from __future__ import annotations

from collections.abc import Iterable

from .types import (
    Arrangement,
    ExcludedResult,
    Listing,
    Profile,
    RemotePref,
    SearchContext,
    seniority_level,
)


def arrangement_allowed(profile: Profile, context: SearchContext, listing: Listing) -> bool:
    """H1: Arrangement acceptance table (ARCHITECTURE.md > Enums and mappings)."""
    if listing.arrangement == Arrangement.REMOTE:
        return True

    same_city = (
        listing.city is not None
        and profile.city is not None
        and listing.city == profile.city
    )

    if context.remote_pref == RemotePref.REMOTE_ONLY:
        return False

    if context.remote_pref == RemotePref.REMOTE_OR_HYBRID:
        if same_city:
            return listing.arrangement == Arrangement.HYBRID
        return profile.relocate

    if context.remote_pref == RemotePref.ANY:
        if same_city:
            return True
        return profile.relocate

    return False


def _arrangement_reason_fa(profile: Profile, listing: Listing) -> str:
    if listing.city and profile.city and listing.city != profile.city:
        return f"آگهی به‌صورت {_arrangement_fa(listing.arrangement)} در {listing.city} است؛ شما در {profile.city} هستید و امکان نقل‌مکان ثبت نکرده‌اید."
    return f"آگهی به‌صورت {_arrangement_fa(listing.arrangement)} است و با ترجیح دورکاری شما مطابقت ندارد."


def _arrangement_fa(arrangement: Arrangement) -> str:
    return {Arrangement.HYBRID: "ترکیبی", Arrangement.ONSITE: "حضوری", Arrangement.REMOTE: "دورکار"}[arrangement]


def _seniority_reason_fa(profile: Profile, listing: Listing) -> str:
    return f"سطح این آگهی ({listing.seniority.value}) خیلی بالاتر از سطح شما ({profile.seniority.value}) است."


def apply_hard_filters(
    profile: Profile, context: SearchContext, listings: Iterable[Listing]
) -> tuple[list[Listing], list[ExcludedResult], int]:
    """Returns (passing_listings, excluded_results, other_path_count).

    H0 (path mismatch) is counted, not listed, per ARCHITECTURE.md > Matching.
    """
    passing: list[Listing] = []
    excluded: list[ExcludedResult] = []
    other_path_count = 0

    for listing in listings:
        if not listing.active:
            continue

        if listing.path != profile.target_path:  # H0
            other_path_count += 1
            continue

        if listing.id in context.hidden_job_ids:  # H5
            excluded.append(ExcludedResult(listing.id, "hidden", "شما این آگهی را پنهان کرده‌اید."))
            continue

        if not arrangement_allowed(profile, context, listing):  # H1
            excluded.append(ExcludedResult(listing.id, "arrangement", _arrangement_reason_fa(profile, listing)))
            continue

        if (
            context.salary_floor_toman is not None
            and listing.salary_max_toman is not None
            and listing.salary_max_toman < context.salary_floor_toman
        ):  # H2
            reason = (
                f"حداکثر حقوق این آگهی ({listing.salary_max_toman:,} تومان) "
                f"کمتر از کف حقوق شما ({context.salary_floor_toman:,} تومان) است."
            )
            excluded.append(ExcludedResult(listing.id, "salary", reason))
            continue

        if context.max_seniority is not None:  # H3, strict ceiling set by DP-2/feedback (too_senior)
            if seniority_level(listing.seniority) > seniority_level(context.max_seniority):
                excluded.append(ExcludedResult(listing.id, "seniority", _seniority_reason_fa(profile, listing)))
                continue
        else:  # H3, default: two or more levels above the user's own seniority
            if seniority_level(listing.seniority) - seniority_level(profile.seniority) >= 2:
                excluded.append(ExcludedResult(listing.id, "seniority", _seniority_reason_fa(profile, listing)))
                continue

        if listing.work_type not in context.work_types:  # H4
            reason = f"نوع همکاری این آگهی ({listing.work_type.value}) با گزینه‌های انتخابی شما مطابقت ندارد."
            excluded.append(ExcludedResult(listing.id, "work_type", reason))
            continue

        passing.append(listing)

    return passing, excluded, other_path_count
