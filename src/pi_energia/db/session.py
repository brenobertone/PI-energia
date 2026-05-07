"""Sessionmaker e context manager de sessão."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session, sessionmaker

from pi_energia.db.engine import get_engine

_engine = get_engine()
SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, future=True)


@contextmanager
def db_session() -> Iterator[Session]:
    s: Session = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
