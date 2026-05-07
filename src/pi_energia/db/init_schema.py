"""Cria o schema SQLite se ainda não existir."""
from __future__ import annotations

from pi_energia.db.engine import get_engine
from pi_energia.db.models import Base


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print("schema criado.")
