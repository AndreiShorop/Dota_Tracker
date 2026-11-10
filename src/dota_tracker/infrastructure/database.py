"""SQLAlchemy engine, session factory, and declarative base.

The engine and session factory are created lazily on first use so the module
can be imported without a live database (e.g. during unit tests that mock the
persistence layer).
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from dota_tracker.infrastructure.settings import AppSettings, load_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine(settings: AppSettings | None = None) -> Engine:
    """Return a cached SQLAlchemy engine for the configured database URL."""
    global _engine
    if _engine is None:
        settings = settings or load_settings()
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def get_session_factory(settings: AppSettings | None = None) -> sessionmaker[Session]:
    """Return a cached session factory bound to the configured engine."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(settings), autoflush=False, autocommit=False
        )
    return _session_factory


def create_session(settings: AppSettings | None = None) -> Session:
    """Create a new ORM session. Callers must close it when done."""
    return get_session_factory(settings)()


def iter_session(settings: AppSettings | None = None) -> Iterator[Session]:
    """Context-managed session helper (yields, then closes)."""
    session = create_session(settings)
    try:
        yield session
    finally:
        session.close()


__all__ = ["Base", "create_session", "get_engine", "get_session_factory", "iter_session"]
