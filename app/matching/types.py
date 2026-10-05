"""Typed data structures for the matching engine (ARCHITECTURE.md > Schemas, Enums and mappings).

Deterministic only (SR-10): nothing in app/matching imports an LLM client.
These are plain dataclasses, not the SQLAlchemy models (T-102) or Pydantic
schemas used at the LLM/web boundary -- matching is a pure function of
(profile, context, listings) and has no reason to depend on either.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class CareerPath(StrEnum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    MOBILE = "mobile"
    DEVOPS = "devops"
    DATA_AI = "data_ai"


class Seniority(StrEnum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"


# Order matters: ARCHITECTURE.md "Enums and mappings" -> Seniority (ordered) intern < junior < mid < senior
SENIORITY_ORDER: tuple[Seniority, ...] = (
    Seniority.INTERN,
    Seniority.JUNIOR,
    Seniority.MID,
    Seniority.SENIOR,
)


def seniority_level(s: Seniority) -> int:
    return SENIORITY_ORDER.index(s)


class RemotePref(StrEnum):
    REMOTE_ONLY = "remote_only"
    REMOTE_OR_HYBRID = "remote_or_hybrid"
    ANY = "any"


class Arrangement(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class WorkType(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    INTERNSHIP = "internship"
    CONTRACT = "contract"


@dataclass(frozen=True)
class Listing:
    id: str
    path: CareerPath
    city: str | None
    arrangement: Arrangement
    work_type: WorkType
    seniority: Seniority
    required_skills: tuple[str, ...]
    preferred_skills: tuple[str, ...]
    salary_min_toman: int | None
    salary_max_toman: int | None
    active: bool = True


@dataclass(frozen=True)
class Profile:
    target_path: CareerPath
    city: str | None
    relocate: bool
    seniority: Seniority
    confirmed_skills: frozenset[str]


@dataclass
class SearchContext:
    """ARCHITECTURE.md > Schemas > search_sessions > SearchContext.

    Only these fields may be changed by feedback (D-16).
    """

    remote_pref: RemotePref
    salary_floor_toman: int | None
    work_types: frozenset[WorkType]
    max_seniority: Seniority | None = None
    hidden_job_ids: frozenset[str] = field(default_factory=frozenset)
    emphasis_skills: frozenset[str] = field(default_factory=frozenset)


@dataclass
class MatchResult:
    job_id: str
    score: int
    label: str | None  # "strong" | "possible" | "weak" | None (not displayed)
    matched: list[str]
    gaps_required: list[str]
    gaps_preferred: list[str]
    considerations: list[str]
    rank: int | None = None


@dataclass
class ExcludedResult:
    job_id: str
    reason_code: str  # path | arrangement | salary | seniority | work_type | hidden | military
    reason_fa: str


@dataclass
class MatchRunResult:
    results: list[MatchResult]
    excluded: list[ExcludedResult]
    other_path_count: int
