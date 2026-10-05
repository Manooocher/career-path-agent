"""T-203: matching core must reproduce docs/ACCEPTANCE.md > Fixtures >
"Expected outcomes for Sara" exactly, for both the initial search and the
state after the golden feedback ("فقط دورکاری، حداقل حقوق ۲۵ میلیون").

Stdlib-only (unittest + json): no third-party deps installed yet (pre-T-101).
    python3 -m unittest tests/unit/test_matching_fixtures.py
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.matching.pipeline import run_match
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


def load(path: str):
    with open(ROOT / path, encoding="utf-8") as f:
        return json.load(f)


def listing_from_fixture(job: dict) -> Listing:
    return Listing(
        id=job["id"],
        path=CareerPath(job["path"]),
        city=job["city"],
        arrangement=Arrangement(job["arrangement"]),
        work_type=WorkType(job["work_type"]),
        seniority=Seniority(job["seniority"]),
        required_skills=tuple(job["required_skills"]),
        preferred_skills=tuple(job["preferred_skills"]),
        salary_min_toman=job["salary_min_toman"],
        salary_max_toman=job["salary_max_toman"],
        active=job["active"],
    )


class SaraFixtureTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        jobs = load("tests/fixtures/jobs_fixtures.json")["jobs"]
        cls.listings = [listing_from_fixture(j) for j in jobs]

        sara = load("tests/fixtures/personas.json")["personas"]["sara"]
        profile_data = sara["profile"]
        confirmed_skills = frozenset(
            s["name_canonical"] for s in sara["evidence"]["skills"] if s["confirmed"]
        )
        cls.profile = Profile(
            target_path=CareerPath(profile_data["target_path"]),
            city=profile_data["city"],
            relocate=profile_data["relocate"],
            seniority=Seniority(profile_data["seniority"]),
            confirmed_skills=confirmed_skills,
        )
        cls.initial_context = SearchContext(
            remote_pref=RemotePref(profile_data["remote_pref"]),
            salary_floor_toman=profile_data["salary_floor_toman"],
            work_types=frozenset(WorkType(w) for w in profile_data["work_types"]),
        )


class TestInitialSearch(SaraFixtureTestCase):
    def setUp(self):
        self.run = run_match(self.profile, self.initial_context, self.listings)
        self.by_id = {r.job_id: r for r in self.run.results}
        self.excluded_by_id = {e.job_id: e for e in self.run.excluded}

    def test_display_order_and_ranks(self):
        # AC-MATCH-001: J02, J01, J07, J03, J04 in that order.
        self.assertEqual(
            [r.job_id for r in self.run.results], ["J02", "J01", "J07", "J03", "J04"]
        )

    def test_scores_and_labels(self):
        expected = {
            "J02": (93, "strong"),
            "J01": (85, "strong"),
            "J07": (80, "strong"),
            "J03": (75, "strong"),
            "J04": (53, "possible"),
        }
        for job_id, (score, label) in expected.items():
            self.assertEqual(self.by_id[job_id].score, score, job_id)
            self.assertEqual(self.by_id[job_id].label, label, job_id)

    def test_j07_unknown_salary_consideration(self):
        self.assertIn("حقوق: نامشخص", self.by_id["J07"].considerations)

    def test_j05_excluded_arrangement(self):
        self.assertEqual(self.excluded_by_id["J05"].reason_code, "arrangement")

    def test_j06_excluded_seniority(self):
        self.assertEqual(self.excluded_by_id["J06"].reason_code, "seniority")

    def test_j08_other_path_counted_not_listed(self):
        self.assertNotIn("J08", self.by_id)
        self.assertNotIn("J08", self.excluded_by_id)
        self.assertEqual(self.run.other_path_count, 1)


class TestAfterGoldenFeedback(SaraFixtureTestCase):
    def setUp(self):
        # Feedback: «فقط دورکاری، حداقل حقوق ۲۵ میلیون» (remote only, floor 25M).
        self.context = SearchContext(
            remote_pref=RemotePref.REMOTE_ONLY,
            salary_floor_toman=25_000_000,
            work_types=self.initial_context.work_types,
        )
        self.run = run_match(self.profile, self.context, self.listings)
        self.by_id = {r.job_id: r for r in self.run.results}
        self.excluded_by_id = {e.job_id: e for e in self.run.excluded}

    def test_j01_unchanged_score_now_rank_1(self):
        self.assertEqual(self.by_id["J01"].score, 85)
        self.assertEqual(self.by_id["J01"].label, "strong")
        self.assertEqual(self.by_id["J01"].rank, 1)

    def test_j02_excluded_salary(self):
        self.assertEqual(self.excluded_by_id["J02"].reason_code, "salary")

    def test_j03_excluded_arrangement_now_hybrid_not_remote(self):
        self.assertEqual(self.excluded_by_id["J03"].reason_code, "arrangement")

    def test_j04_unchanged(self):
        self.assertEqual(self.by_id["J04"].score, 53)
        self.assertEqual(self.by_id["J04"].label, "possible")

    def test_j05_still_excluded_arrangement(self):
        self.assertEqual(self.excluded_by_id["J05"].reason_code, "arrangement")

    def test_j06_still_excluded_seniority(self):
        self.assertEqual(self.excluded_by_id["J06"].reason_code, "seniority")

    def test_j07_unchanged(self):
        self.assertEqual(self.by_id["J07"].score, 80)
        self.assertEqual(self.by_id["J07"].label, "strong")

    def test_at_least_three_listings_remain(self):
        # AC-FBK-002 (deployed-DB phrasing, also holds for the fixture DB here).
        self.assertGreaterEqual(len(self.run.results), 3)

    def test_no_shown_listing_is_hybrid_onsite_or_low_salary(self):
        for result in self.run.results:
            listing = next(l for l in self.listings if l.id == result.job_id)
            self.assertEqual(listing.arrangement, Arrangement.REMOTE)
            if listing.salary_max_toman is not None:
                self.assertGreaterEqual(listing.salary_max_toman, 25_000_000)


if __name__ == "__main__":
    unittest.main()
