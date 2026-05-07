"""Ingestão SUBESTACAO.parquet → stg_subestacao."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import delete

from pi_energia.config import SUBESTACAO_PARQUET
from pi_energia.db.models import StgSubestacao
from pi_energia.db.session import db_session


def ingest_stg_subestacao() -> int:
    df = pd.read_parquet(SUBESTACAO_PARQUET)
    df = df.rename(columns={
        "val_latitude": "lat",
        "val_longitude": "lon",
        "nom_agente_principal": "_agente",
        "id_estacao": "_estacao",
        "num_barra": "_barra",
        "nom_subsistema": "_nom_sub",
        "nom_estado": "_nom_est",
    })
    df = df[["id_subestacao", "nom_subestacao", "id_subsistema", "id_estado",
             "lat", "lon"]].copy()
    df["id_subestacao"] = df["id_subestacao"].str.strip().str.upper()
    for col in ("lat", "lon"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # uma linha por subestação (coordenadas são as mesmas entre tensões)
    df = df.drop_duplicates(subset=["id_subestacao"])
    df = df.where(pd.notnull(df), None)

    rows = df.to_dict(orient="records")
    with db_session() as s:
        s.execute(delete(StgSubestacao))
        s.bulk_insert_mappings(StgSubestacao, rows)
    return len(rows)


if __name__ == "__main__":
    print("stg_subestacao:", ingest_stg_subestacao())
