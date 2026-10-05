"""T-202a: fixtures and taxonomy seed must match docs/ACCEPTANCE.md exactly (AC-DATA-002).

Stdlib-only (unittest + json): no app code exists yet (pre-T-101), so this
suite must run with nothing but python3, e.g.:

    python3 -m unittest tests/unit/test_fixtures_taxonomy.py
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CAREER_PATHS = {"frontend", "backend", "fullstack", "mobile", "devops", "data_ai"}

# docs/ACCEPTANCE.md > Fixtures > Listings J01-J08
EXPECTED_JOBS = {
    "J01": dict(title="Junior React Developer", arrangement="remote", city=None, seniority="junior",
                required=["React", "JavaScript", "Git"], preferred=["TypeScript"],
                salary_min=28_000_000, salary_max=35_000_000, path="frontend"),
    "J02": dict(title="Frontend Intern", arrangement="remote", city=None, seniority="intern",
                required=["HTML", "CSS", "JavaScript"], preferred=[],
                salary_min=12_000_000, salary_max=18_000_000, path="frontend"),
    "J03": dict(title="Junior Frontend Developer (Vue)", arrangement="hybrid", city="شیراز", seniority="junior",
                required=["Vue", "JavaScript", "CSS"], preferred=[],
                salary_min=22_000_000, salary_max=30_000_000, path="frontend"),
    "J04": dict(title="Junior Next.js Developer", arrangement="remote", city=None, seniority="junior",
                required=["React", "Next.js", "TypeScript"], preferred=[],
                salary_min=25_000_000, salary_max=32_000_000, path="frontend"),
    "J05": dict(title="React Developer", arrangement="onsite", city="تهران", seniority="junior",
                required=["React", "JavaScript"], preferred=[],
                salary_min=30_000_000, salary_max=40_000_000, path="frontend"),
    "J06": dict(title="Senior Frontend Engineer", arrangement="remote", city=None, seniority="senior",
                required=["React", "TypeScript", "Testing"], preferred=[],
                salary_min=55_000_000, salary_max=70_000_000, path="frontend"),
    "J07": dict(title="Junior Frontend Developer", arrangement="remote", city=None, seniority="junior",
                required=["React", "CSS"], preferred=["TypeScript", "Tailwind CSS"],
                salary_min=None, salary_max=None, path="frontend"),
    "J08": dict(title="Backend Intern (Python)", arrangement="remote", city=None, seniority="intern",
                required=["Python", "Django", "SQL"], preferred=[],
                salary_min=20_000_000, salary_max=25_000_000, path="backend"),
}

# docs/ACCEPTANCE.md > Fixtures > Persona: Sara
EXPECTED_SARA_PROFILE = dict(
    target_path="frontend", city="شیراز", relocate=False, seniority="junior",
    years_experience=0.5, remote_pref="remote_or_hybrid",
    work_types=["full_time", "internship"], salary_floor_toman=15_000_000,
)
EXPECTED_SARA_SKILLS = {"HTML", "CSS", "JavaScript", "React", "Git"}


def load(path: str):
    with open(ROOT / path, encoding="utf-8") as f:
        return json.load(f)


class TestPaths(unittest.TestCase):
    def test_six_career_paths_exactly(self):
        data = load("data/taxonomy/paths.json")
        ids = {p["id"] for p in data["paths"]}
        self.assertEqual(ids, CAREER_PATHS)
        for p in data["paths"]:
            self.assertTrue(p.get("label_fa"), f"{p['id']} missing label_fa")
            self.assertTrue(p.get("label_en"), f"{p['id']} missing label_en")


class TestSkillsTaxonomy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skills = load("data/taxonomy/skills.json")["skills"]
        cls.canonical = {s["canonical"] for s in cls.skills}

    def test_every_skill_has_fa_and_en_aliases(self):
        for s in self.skills:
            self.assertTrue(s.get("aliases_en"), f"{s['canonical']} missing English aliases")
            self.assertTrue(s.get("aliases_fa"), f"{s['canonical']} missing Persian aliases")
            self.assertTrue(s.get("paths"), f"{s['canonical']} missing path tags")
            for p in s["paths"]:
                self.assertIn(p, CAREER_PATHS)

    def test_no_duplicate_canonical_names(self):
        names = [s["canonical"] for s in self.skills]
        self.assertEqual(len(names), len(set(names)), "duplicate canonical skill name")

    def test_covers_every_fixture_job_skill(self):
        jobs = load("tests/fixtures/jobs_fixtures.json")["jobs"]
        for job in jobs:
            for skill in job["required_skills"] + job["preferred_skills"]:
                self.assertIn(skill, self.canonical, f"{job['id']} needs uncovered skill {skill!r}")

    def test_covers_sara_skills_and_project_technologies(self):
        sara = load("tests/fixtures/personas.json")["personas"]["sara"]
        for skill in sara["evidence"]["skills"]:
            self.assertIn(skill["name_canonical"], self.canonical)
        for project in sara["evidence"]["projects"]:
            for tech in project["technologies"]:
                self.assertIn(tech, self.canonical)


class TestJobsFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jobs = {j["id"]: j for j in load("tests/fixtures/jobs_fixtures.json")["jobs"]}

    def test_exactly_j01_to_j08(self):
        self.assertEqual(set(self.jobs.keys()), set(EXPECTED_JOBS.keys()))

    def test_every_job_is_a_fixture_and_active(self):
        for job in self.jobs.values():
            self.assertTrue(job["is_fixture"])
            self.assertTrue(job["active"])
            self.assertEqual(job["enrichment_version"], 1)

    def test_fields_match_acceptance_exactly(self):
        for job_id, expected in EXPECTED_JOBS.items():
            job = self.jobs[job_id]
            self.assertEqual(job["title"], expected["title"], job_id)
            self.assertEqual(job["arrangement"], expected["arrangement"], job_id)
            self.assertEqual(job["city"], expected["city"], job_id)
            self.assertEqual(job["seniority"], expected["seniority"], job_id)
            self.assertEqual(job["required_skills"], expected["required"], job_id)
            self.assertEqual(job["preferred_skills"], expected["preferred"], job_id)
            self.assertEqual(job["salary_min_toman"], expected["salary_min"], job_id)
            self.assertEqual(job["salary_max_toman"], expected["salary_max"], job_id)
            self.assertEqual(job["path"], expected["path"], job_id)

    def test_j07_salary_unknown_not_zero(self):
        # D-17: unknown salary ("توافقی") is neutral, never treated as 0.
        j07 = self.jobs["J07"]
        self.assertIsNone(j07["salary_min_toman"])
        self.assertIsNone(j07["salary_max_toman"])

    def test_source_urls_are_unique(self):
        urls = [j["source_url"] for j in self.jobs.values()]
        self.assertEqual(len(urls), len(set(urls)))

    def test_no_pii_markers_in_company_or_excerpt(self):
        # Fixtures are fictional; guard against accidental emails/phone numbers.
        for job in self.jobs.values():
            for field in ("company", "excerpt_fa"):
                text = job[field]
                self.assertNotIn("@", text, f"{job['id']}.{field}")
                self.assertFalse(any(ch.isdigit() for ch in text), f"{job['id']}.{field} contains digits")


class TestSaraPersona(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sara = load("tests/fixtures/personas.json")["personas"]["sara"]

    def test_profile_matches_acceptance(self):
        profile = self.sara["profile"]
        for key, value in EXPECTED_SARA_PROFILE.items():
            self.assertEqual(profile[key], value, key)

    def test_confirmed_skills_match_acceptance(self):
        names = {s["name_canonical"] for s in self.sara["evidence"]["skills"]}
        self.assertEqual(names, EXPECTED_SARA_SKILLS)
        for s in self.sara["evidence"]["skills"]:
            self.assertTrue(s["confirmed"])

    def test_two_projects_with_expected_technologies(self):
        projects = {p["title"]: p for p in self.sara["evidence"]["projects"]}
        self.assertEqual(set(projects.keys()), {"Bookshelf", "Weather widget"})
        self.assertEqual(set(projects["Bookshelf"]["technologies"]), {"React", "JavaScript", "CSS"})
        self.assertEqual(set(projects["Weather widget"]["technologies"]), {"JavaScript", "HTML", "CSS"})

    def test_no_invented_institution(self):
        # ACCEPTANCE.md gives no institution name for Sara's degree; the honesty
        # rule (PRODUCT.md §5) forbids stating one that isn't in evidence.
        self.assertIsNone(self.sara["evidence"]["education"][0]["institution"])


if __name__ == "__main__":
    unittest.main()
