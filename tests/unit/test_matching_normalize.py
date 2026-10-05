"""T-203: ARCHITECTURE.md > Normalization.

    python3 -m unittest tests/unit/test_matching_normalize.py
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.matching.normalize import (
    load_skills_taxonomy,
    normalize_digits,
    normalize_money,
    normalize_skill,
    normalize_text,
)


class TestDigitsAndText(unittest.TestCase):
    def test_persian_and_arabic_indic_digits_to_ascii(self):
        self.assertEqual(normalize_digits("۲۵"), "25")
        self.assertEqual(normalize_digits("٢٥"), "25")

    def test_arabic_letterforms_to_persian(self):
        self.assertEqual(normalize_text("علي"), "علی")  # ي -> ی
        self.assertEqual(normalize_text("كار"), "کار")  # ك -> ک

    def test_kashida_removed(self):
        self.assertEqual(normalize_text("سلاـــم"), "سلام")

    def test_collapses_whitespace(self):
        self.assertEqual(normalize_text("سلام   دنیا"), "سلام دنیا")

    def test_zwnj_kept_for_display_removed_for_matching_key(self):
        text = "می‌خواهم"  # contains ZWNJ
        self.assertIn("‌", normalize_text(text))
        self.assertNotIn("‌", normalize_text(text, for_matching_key=True))

    def test_idempotent(self):
        for text in ["علي  كار", "می‌خواهم", "  a  b  "]:
            once = normalize_text(text)
            self.assertEqual(normalize_text(once), once)


class TestMoney(unittest.TestCase):
    def test_the_three_equivalent_forms_from_architecture(self):
        self.assertEqual(normalize_money("۲۵ میلیون"), 25_000_000)
        self.assertEqual(normalize_money("25M"), 25_000_000)
        self.assertEqual(normalize_money("25 تومن"), 25_000_000)

    def test_rial_divided_by_ten(self):
        self.assertEqual(normalize_money("250000000 ریال"), 25_000_000)

    def test_unknown_markers(self):
        for text in ["توافقی", "Negotiable", "نامشخص"]:
            self.assertIsNone(normalize_money(text))

    def test_none_passthrough(self):
        self.assertIsNone(normalize_money(None))

    def test_thousand_word_explicit(self):
        self.assertEqual(normalize_money("25 هزار تومان"), 25_000)

    def test_large_figure_not_multiplied(self):
        # Already a full Toman figure; must not be treated as "in millions".
        self.assertEqual(normalize_money("28000000 تومان"), 28_000_000)


class TestSkillTaxonomy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.alias_map = load_skills_taxonomy()

    def test_known_english_alias(self):
        canonical, known = normalize_skill("reactjs", self.alias_map)
        self.assertTrue(known)
        self.assertEqual(canonical, "React")

    def test_known_persian_alias(self):
        canonical, known = normalize_skill("ری‌اکت", self.alias_map)
        self.assertTrue(known)
        self.assertEqual(canonical, "React")

    def test_known_persian_alias_django(self):
        canonical, known = normalize_skill("جنگو", self.alias_map)
        self.assertTrue(known)
        self.assertEqual(canonical, "Django")

    def test_known_persian_alias_python(self):
        canonical, known = normalize_skill("پایتون", self.alias_map)
        self.assertTrue(known)
        self.assertEqual(canonical, "Python")

    def test_known_k8s_alias(self):
        canonical, known = normalize_skill("k8s", self.alias_map)
        self.assertTrue(known)
        self.assertEqual(canonical, "Kubernetes")

    def test_unknown_skill_kept_and_flagged(self):
        canonical, known = normalize_skill("CobolMaster9000", self.alias_map)
        self.assertFalse(known)
        self.assertEqual(canonical, "CobolMaster9000")

    def test_idempotent_on_canonical_form(self):
        first, _ = normalize_skill("reactjs", self.alias_map)
        second, known = normalize_skill(first, self.alias_map)
        self.assertEqual(first, second)
        self.assertTrue(known)


if __name__ == "__main__":
    unittest.main()
