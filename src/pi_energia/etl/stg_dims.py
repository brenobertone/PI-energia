"""Popula as dimensões básicas a partir de config."""
from __future__ import annotations

from sqlalchemy import delete, select

from pi_energia.config import SUBSISTEMAS
from pi_energia.db.models import DimSubsistema
from pi_energia.db.session import db_session


def build_dims() -> dict[str, int]:
    with db_session() as s:
        s.execute(delete(DimSubsistema))
        s.flush()
        for sigla, nome in SUBSISTEMAS:
            s.add(DimSubsistema(sigla=sigla, nome=nome))
        s.flush()

        return {
            "subsistemas": len(s.execute(select(DimSubsistema)).scalars().all()),
        }


if __name__ == "__main__":
    print(build_dims())
