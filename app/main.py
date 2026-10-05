"""App factory (ARCHITECTURE.md > Repo layout > app/main.py).

Startup here is deliberately thin for T-101: settings load fail-fast
(app/config.py) and a DB connectivity probe. The migrate-check and
stale-run-recovery steps mentioned in ARCHITECTURE.md belong to T-102
(Alembic) and T-301 (runner) respectively -- they are not implemented yet
and this module does not pretend otherwise.
"""
from __future__ import annotations

from fastapi import FastAPI

from app.config import get_settings
from app.db import check_db

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(title="CareerPath")

    @app.get("/healthz")
    def healthz() -> dict:
        return {
            "db": "ok" if check_db() else "error",
            "llm_config": "ok" if settings.llm_configured else "not_configured",
        }

    return app


app = create_app()
