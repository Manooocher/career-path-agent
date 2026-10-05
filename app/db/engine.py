"""SQLAlchemy engine/session (ARCHITECTURE.md > Repo layout > app/db/).

SQLAlchemy models themselves land in T-102 (Database baseline); this file
only sets up the engine and a connectivity probe for /healthz.
"""
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def check_db() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 -- /healthz must report "error", never crash, on any DB failure
        return False
