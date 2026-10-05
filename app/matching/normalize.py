"""ARCHITECTURE.md > Normalization. Applied to every user input and to every
listing during ingestion. Pure functions only; idempotent by construction
(normalize(normalize(x)) == normalize(x)) -- see tests/unit/test_matching_properties.py.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SKILLS_TAXONOMY_PATH = REPO_ROOT / "data" / "taxonomy" / "skills.json"

_ARABIC_YEH = "ي"  # ي
_PERSIAN_YEH = "ی"  # ی
_ARABIC_KAF = "ك"  # ك
_PERSIAN_KAF = "ک"  # ک
_KASHIDA = "ـ"  # ـ (tatweel)
_ZWNJ = "‌"

_PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC_INDIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_ASCII_DIGITS = "0123456789"
_DIGIT_MAP = {ch: d for ch, d in zip(_PERSIAN_DIGITS, _ASCII_DIGITS)}
_DIGIT_MAP.update({ch: d for ch, d in zip(_ARABIC_INDIC_DIGITS, _ASCII_DIGITS)})

_THOUSANDS_SEPARATORS = {",", "٬"}  # ASCII comma, Arabic thousands separator


def normalize_digits(text: str) -> str:
    """Persian and Arabic-Indic digits -> ASCII, before any number parsing."""
    return "".join(_DIGIT_MAP.get(ch, ch) for ch in text)


def normalize_text(text: str, *, for_matching_key: bool = False) -> str:
    """Character-level normalization: Arabic -> Persian letterforms, strip
    kashida, collapse whitespace. ZWNJ is kept for display but removed when
    the result is used as a matching key (e.g. skill/city lookup).
    """
    text = text.replace(_ARABIC_YEH, _PERSIAN_YEH).replace(_ARABIC_KAF, _PERSIAN_KAF)
    text = text.replace(_KASHIDA, "")
    if for_matching_key:
        text = text.replace(_ZWNJ, "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_city(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    normalized = normalize_text(text)
    return normalized or None


_UNKNOWN_SALARY_MARKERS = ("توافقی", "negotiable", "نامشخص", "unknown")
_MILLION_WORDS = ("میلیون",)
_THOUSAND_WORDS = ("هزار",)
_RIAL_WORDS = ("ریال", "rial")
_SMALL_FIGURE_IS_MILLIONS_THRESHOLD = 1000


def normalize_money(text: Optional[str]) -> Optional[int]:
    """«۲۵ میلیون», "25M", "25 تومن" -> 25,000,000 (Toman). «ریال» values
    are divided by 10. «توافقی» and friends -> None (unknown, D-17).

    Colloquial convention: a bare figure under 1000 with no explicit
    magnitude word is stated in millions of Toman ("۲۵ تومن" == 25M Toman),
    matching how Iranian salary figures are actually spoken/written.
    """
    if text is None:
        return None
    s = normalize_digits(str(text))
    s = normalize_text(s).lower()
    for sep in _THOUSANDS_SEPARATORS:
        s = s.replace(sep, "")
    s = s.strip()
    if not s or any(marker in s for marker in _UNKNOWN_SALARY_MARKERS):
        return None

    match = re.search(r"\d+(?:\.\d+)?", s)
    if not match:
        return None
    value = float(match.group())

    has_million = any(w in s for w in _MILLION_WORDS) or bool(re.search(r"\d\s*m\b", s))
    has_thousand = any(w in s for w in _THOUSAND_WORDS) or bool(re.search(r"\d\s*k\b", s))
    is_rial = any(w in s for w in _RIAL_WORDS)

    if has_million:
        value *= 1_000_000
    elif has_thousand:
        value *= 1_000
    elif value < _SMALL_FIGURE_IS_MILLIONS_THRESHOLD:
        value *= 1_000_000

    if is_rial:
        value /= 10

    return int(round(value))


def _normalize_en_skill_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _normalize_fa_skill_key(text: str) -> str:
    return normalize_text(text, for_matching_key=True).replace(" ", "")


def load_skills_taxonomy(path: Optional[Path] = None) -> Dict[str, str]:
    """Build an alias -> canonical skill lookup from data/taxonomy/skills.json.
    Canonical names map to themselves, which is what makes normalize_skill
    idempotent.
    """
    path = path or DEFAULT_SKILLS_TAXONOMY_PATH
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    alias_to_canonical: Dict[str, str] = {}
    for skill in data["skills"]:
        canonical = skill["canonical"]
        alias_to_canonical[_normalize_en_skill_key(canonical)] = canonical
        for alias in skill.get("aliases_en", []):
            alias_to_canonical[_normalize_en_skill_key(alias)] = canonical
        for alias in skill.get("aliases_fa", []):
            alias_to_canonical[_normalize_fa_skill_key(alias)] = canonical
    return alias_to_canonical


def normalize_skill(raw: str, alias_map: Dict[str, str]) -> Tuple[str, bool]:
    """Returns (canonical_or_original, is_known). Unknown skills are kept as
    entered and flagged, per ARCHITECTURE.md > Normalization > Skills.
    """
    digits_fixed = normalize_digits(raw)
    en_key = _normalize_en_skill_key(digits_fixed)
    if en_key and en_key in alias_map:
        return alias_map[en_key], True
    fa_key = _normalize_fa_skill_key(digits_fixed)
    if fa_key in alias_map:
        return alias_map[fa_key], True
    return normalize_text(raw).strip(), False
