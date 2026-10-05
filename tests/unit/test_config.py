"""T-101: app/config.py must fail fast and clearly (Done when: "missing env
var stops startup clearly"), and must enforce the production safety rules
(SR-09) and the scraping delay floor (D-22, SR-11).

Requires the project's declared dependencies (pydantic-settings et al.),
unlike the stdlib-only matching tests. Run inside the venv or the app
container -- see CLAUDE.md > Commands.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pydantic import ValidationError

from app.config import Settings

BASE_ENV = {
    "APP_ENV": "development",
    "SECRET_KEY": "a-dev-secret-key-of-sufficient-length",
    "DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/careerpath",
}


def settings_with(**overrides):
    env = {**BASE_ENV, **overrides}
    with mock.patch.dict(os.environ, env, clear=True):
        return Settings(_env_file=None)


class TestRequiredFields(unittest.TestCase):
    def test_valid_minimal_env_succeeds(self):
        settings_with()  # must not raise

    def test_missing_app_env_fails(self):
        env = dict(BASE_ENV)
        del env["APP_ENV"]
        with self.assertRaises(ValidationError) as ctx:
            with mock.patch.dict(os.environ, env, clear=True):
                Settings(_env_file=None)
        self.assertIn("app_env", str(ctx.exception).lower())

    def test_blank_database_url_fails(self):
        with self.assertRaises(ValidationError):
            settings_with(DATABASE_URL="")

    def test_short_secret_key_fails(self):
        with self.assertRaises(ValidationError):
            settings_with(SECRET_KEY="too-short")

    def test_invalid_app_env_value_fails(self):
        with self.assertRaises(ValidationError):
            settings_with(APP_ENV="staging")


class TestProductionSafety(unittest.TestCase):
    def test_production_with_fault_injection_fails(self):
        with self.assertRaises(ValidationError) as ctx:
            settings_with(APP_ENV="production", FAULT_INJECTION="error", LLM_API_KEY="sk-x")
        self.assertIn("SR-09", str(ctx.exception))

    def test_production_without_llm_key_fails(self):
        with self.assertRaises(ValidationError):
            settings_with(APP_ENV="production")

    def test_production_with_fault_off_and_llm_key_succeeds(self):
        settings = settings_with(APP_ENV="production", FAULT_INJECTION="off", LLM_API_KEY="sk-x")
        self.assertTrue(settings.llm_api_key)

    def test_development_allows_fault_injection_and_no_llm_key(self):
        settings_with(APP_ENV="development", FAULT_INJECTION="error")  # must not raise


class TestScrapingDelayFloor(unittest.TestCase):
    def test_delay_below_three_seconds_fails(self):
        with self.assertRaises(ValidationError) as ctx:
            settings_with(INGEST_DELAY_S="1")
        self.assertIn("D-22", str(ctx.exception))

    def test_delay_of_three_seconds_succeeds(self):
        settings_with(INGEST_DELAY_S="3")  # must not raise


class TestLlmConfiguredProperty(unittest.TestCase):
    def test_not_configured_when_any_llm_field_blank(self):
        self.assertFalse(settings_with().llm_configured)

    def test_configured_when_all_llm_fields_set(self):
        settings = settings_with(
            LLM_API_KEY="sk-x", LLM_MODELS_FAST="model-a", LLM_MODELS_SMART="model-b"
        )
        self.assertTrue(settings.llm_configured)


if __name__ == "__main__":
    unittest.main()
