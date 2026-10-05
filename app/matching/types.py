"""Typed data structures for the matching engine (ARCHITECTURE.md > Schemas, Enums and mappings).

Deterministic only (SR-10): nothing in app/matching imports an LLM client.
These are plain dataclasses, not the SQLAlchemy models (T-102) or Pydantic
schemas used at the LLM/web boundary -- matching is a pure function of
(profile, context, listings) and has no reason to depend on either.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet, List, Optional, Tuple


class CareerPath(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    MOBILE = "mobile"
    DEVOPS = "devops"
    DATA_AI = "data_ai"


class Seniority(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"


# Order matters: ARCHITECTURE.md "Enums and mappings" -> Seniority (ordered) intern < junior < mid < senior
SENIORITY_ORDER: Tuple[Seniority, ...] = (
    Seniority.INTERN,
    Seniority.JUNIOR,
    Seniority.MID,
    Seniority.SENIOR,
)


def seniority_level(s: Seniority) -> int:
    return SENIORITY_ORDER.index(s)


class RemotePref(str, Enum):
    REMOTE_ONLY = "remote_only"
    REMOTE_OR_HYBRID = "remote_or_hybrid"
    ANY = "any"


class Arrangement(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class WorkType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    INTERNSHIP = "internship"
    CONTRACT = "contract"


@dataclass(frozen=True)
class Listing:
    id: str
    path: CareerPath
    city: Optional[str]
    arrangement: Arrangement
    work_type: WorkType
    seniority: Seniority
    required_skills: Tuple[str, ...]
    preferred_skills: Tuple[str, ...]
    salary_min_toman: Optional[int]
    salary_max_toman: Optional[int]
    active: bool = True


@dataclass(frozen=True)
class Profile:
    target_path: CareerPath
    city: Optional[str]
    relocate: bool
    seniority: Seniority
    confirmed_skills: FrozenSet[str]


@dataclass
class SearchContext:
    """ARCHITECTURE.md > Schemas > search_sessions > SearchContext.

    Only these fields may be changed by feedback (D-16).
    """

    remote_pref: RemotePref
    salary_floor_toman: Optional[int]
    work_types: FrozenSet[WorkType]
    max_seniority: Optional[Seniority] = None
    hidden_job_ids: FrozenSet[str] = field(default_factory=frozenset)
    emphasis_skills: FrozenSet[str] = field(default_factory=frozenset)


@dataclass
class MatchResult:
    job_id: str
    score: int
    label: Optional[str]  # "strong" | "possible" | "weak" | None (not displayed)
    matched: List[str]
    gaps_required: List[str]
    gaps_preferred: List[str]
    considerations: List[str]
    rank: Optional[int] = None


@dataclass
class ExcludedResult:
    job_id: str
    reason_code: str  # path | arrangement | salary | seniority | work_type | hidden | military
    reason_fa: str


@dataclass
class MatchRunResult:
    results: List[MatchResult]
    excluded: List[ExcludedResult]
    other_path_count: int
