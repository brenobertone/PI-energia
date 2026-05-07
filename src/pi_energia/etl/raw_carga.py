"""Ingestão ONS — carga diária de energia por subsistema."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import delete

from pi_energia.config import CARGA_PARQUET
from pi_energia.db.models import RawCargaEnergia
from pi_energia.db.session import db_session


def ingest_raw_carga() -> int:
    df = pd.read_parquet(CARGA_PARQUET)
    src = CARGA_PARQUET.name
    rows = [
        {
            "id_subsistema": r.id_subsistema,
            "nom_subsistema": r.nom_subsistema,
            "din_instante": r.din_instante.to_pydatetime(),
            "val_cargaenergiamwmed": float(r.val_cargaenergiamwmed),
            "source_file": src,
        }
        for r in df.itertuples(index=False)
    ]
    with db_session() as s:
        s.execute(delete(RawCargaEnergia).where(RawCargaEnergia.source_file == src))
        s.bulk_insert_mappings(RawCargaEnergia, rows)
    return len(rows)


if __name__ == "__main__":
    print("raw_carga_energia:", ingest_raw_carga())
