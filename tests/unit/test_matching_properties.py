"""T-203: ARCHITECTURE.md > Matching > Properties (unit-tested).

    python3 -m unittest tests/unit/test_matching_properties.py
"""
import itertools
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.matching.filters import apply_hard_filters
from app.matching.normalize import normalize_text
from app.matching.pipeline import run_match
from app.matching.scoring import score_listing
from app.matching.types import (
    Arrangement,
    CareerPath,
    Listing,
    Profile,
    RemotePref,
    SearchContext,
    Seniority,
    WorkType,
)


def make_listing(**overrides) -> Listing:
    defaults = dict(
        id="L1",
        path=CareerPath.FRONTEND,
        city=None,
        arrangement=Arrangement.REMOTE,
        work_type=WorkType.FULL_TIME,
        seniority=Seniority.JUNIOR,
        required_skills=("React", "JavaScript"),
        preferred_skills=("TypeScript",),
        salary_min_toman=20_000_000,
        salary_max_toman=30_000_000,
        active=True,
    )
    defaults.update(overrides)
    return Listing(**defaults)


def make_profile(**overrides) -> Profile:
    defaults = dict(
        target_path=CareerPath.FRONTEND,
        city="شیراز",
        relocate=False,
        seniority=Seniority.JUNIOR,
        confirmed_skills=frozenset({"React", "JavaScript"}),
    )
    defaults.update(overrides)
    return Profile(**defaults)


def make_context(**overrides) -> SearchContext:
    defaults = dict(
        remote_pref=RemotePref.ANY,
        salary_floor_toman=15_000_000,
        work_types=frozenset({WorkType.FULL_TIME, WorkType.INTERNSHIP}),
    )
    defaults.update(overrides)
    return SearchContext(**defaults)


SKILL_POOL = ["React", "JavaScript", "TypeScript", "CSS", "HTML", "Git", "Vue"]


class TestBounds(unittest.TestCase):
    def test_score_always_in_0_100(self):
        for r_size, p_size, s_size, seniority, salary_min in itertools.product(
            range(4), range(3), range(4), list(Seniority), [None, 10_000_000, 50_000_000]
        ):
            listing = make_listing(
                required_skills=tuple(SKILL_POOL[:r_size]),
                preferred_skills=tuple(SKILL_POOL[r_size : r_size + p_size]),
                seniority=seniority,
                salary_min_toman=salary_min,
                salary_max_toman=salary_min,
            )
            profile = make_profile(confirmed_skills=frozenset(SKILL_POOL[:s_size]))
            context = make_context()
            result = score_listing(profile, context, listing)
            self.assertGreaterEqual(result.score, 0)
            self.assertLessEqual(result.score, 100)


class TestDeterminism(unittest.TestCase):
    def test_same_inputs_same_results_and_order(self):
        listings = [
            make_listing(id="L1", required_skills=("React",)),
            make_listing(id="L2", required_skills=("Vue",), salary_min_toman=5_000_000, salary_max_toman=8_000_000),
            make_listing(id="L3", seniority=Seniority.SENIOR),
        ]
        profile = make_profile()
        context = make_context()

        run1 = run_match(profile, context, listings)
        run2 = run_match(profile, context, listings)

        self.assertEqual([r.job_id for r in run1.results], [r.job_id for r in run2.results])
        self.assertEqual([r.score for r in run1.results], [r.score for r in run2.results])
        self.assertEqual({e.job_id for e in run1.excluded}, {e.job_id for e in run2.excluded})


class TestMonotonicFilters(unittest.TestCase):
    def setUp(self):
        self.listings = [
            make_listing(id="L1", arrangement=Arrangement.REMOTE),
            make_listing(id="L2", arrangement=Arrangement.HYBRID, city="شیراز"),
            make_listing(id="L3", arrangement=Arrangement.ONSITE, city="تهران"),
            make_listing(id="L4", seniority=Seniority.SENIOR),
            make_listing(id="L5", work_type=WorkType.CONTRACT),
            make_listing(id="L6", salary_min_toman=1_000_000, salary_max_toman=5_000_000),
        ]
        self.profile = make_profile()

    def _passing_ids(self, context):
        passing, _, _ = apply_hard_filters(self.profile, context, self.listings)
        return {l.id for l in passing}

    def test_raising_salary_floor_never_adds_listings(self):
        loose = self._passing_ids(make_context(salary_floor_toman=1_000_000))
        strict = self._passing_ids(make_context(salary_floor_toman=15_000_000))
        self.assertTrue(strict.issubset(loose))

    def test_hiding_a_listing_never_adds_listings(self):
        base = self._passing_ids(make_context())
        with_hidden = self._passing_ids(make_context(hidden_job_ids=frozenset({"L1"})))
        self.assertTrue(with_hidden.issubset(base))
        self.assertNotIn("L1", with_hidden)

    def test_tightening_remote_pref_never_adds_listings(self):
        loose = self._passing_ids(make_context(remote_pref=RemotePref.ANY))
        strict = self._passing_ids(make_context(remote_pref=RemotePref.REMOTE_ONLY))
        self.assertTrue(strict.issubset(loose))

    def test_setting_max_seniority_never_adds_listings(self):
        loose = self._passing_ids(make_context())
        strict = self._passing_ids(make_context(max_seniority=Seniority.JUNIOR))
        self.assertTrue(strict.issubset(loose))


class TestIdempotentNormalization(unittest.TestCase):
    def test_normalize_text_is_idempotent(self):
        for text in ["كتاب  علي", "می‌خواهم", "", "   "]:
            once = normalize_text(text)
            self.assertEqual(normalize_text(once), once)


class TestNoDivisionByZero(unittest.TestCase):
    def test_empty_required_preferred_emphasis(self):
        listing = make_listing(required_skills=(), preferred_skills=())
        profile = make_profile(confirmed_skills=frozenset())
        context = make_context(emphasis_skills=frozenset())
        result = score_listing(profile, context, listing)  # must not raise
        self.assertIn("نیازمندی‌ها مشخص نشده", result.considerations)
        self.assertGreaterEqual(result.score, 0)

    def test_empty_listings_list(self):
        run = run_match(make_profile(), make_context(), [])  # must not raise
        self.assertEqual(run.results, [])
        self.assertEqual(run.excluded, [])
        self.assertEqual(run.other_path_count, 0)


if __name__ == "__main__":
    unittest.main()
