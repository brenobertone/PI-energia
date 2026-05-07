"""Ingestão ANEEL SIGET — Contrato Módulo Linha Transmissão."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import delete

from pi_energia.config import SIGET_LINHA_CSV
from pi_energia.db.models import RawSigetLinha
from pi_energia.db.session import db_session


def _to_num(x):
    if x is None or pd.isna(x):
        return None
    s = str(x).replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def ingest_raw_siget_linha() -> int:
    df = pd.read_csv(SIGET_LINHA_CSV, sep=";", encoding="latin1", low_memory=False)
    df["NumEtnLinTms_km"] = df["NumEtnLinTms"].map(_to_num)
    df["NumTensaoBaseLinhaTransm_kV"] = df["NumTensaoBaseLinhaTransm"].map(_to_num)

    cols = [
        ("IdeMdl", "IdeMdl"),
        ("IdeLinTms", "IdeLinTms"),
        ("DscSitLinTms", "DscSitLinTms"),
        ("NomLinTms", "NomLinTms"),
        ("NumCcuLinTms", "NumCcuLinTms"),
        ("NumEtnLinTms_km", "NumEtnLinTms_km"),
        ("NumTensaoBaseLinhaTransm_kV", "NumTensaoBaseLinhaTransm_kV"),
        ("IdcTipoCircuitoLinhaTransm", "IdcTipoCircuitoLinhaTransm"),
        ("IdeOnsSbeOrigem", "IdeOnsSbeOrigem"),
        ("NomSubestacaoOrigem", "NomSubestacaoOrigem"),
        ("SigUFSubestacaoOrigem", "SigUFSubestacaoOrigem"),
        ("IdeOnsSbeDestino", "IdeOnsSbeDestino"),
        ("NomSubestacaoDestino", "NomSubestacaoDestino"),
        ("SigUFSubestacaoDestino", "SigUFSubestacaoDestino"),
    ]
    src = SIGET_LINHA_CSV.name
    rows = []
    for _, r in df.iterrows():
        d = {}
        for out, src_col in cols:
            v = r.get(src_col)
            if isinstance(v, float) and pd.isna(v):
                v = None
            d[out] = v
        d["source_file"] = src
        rows.append(d)

    with db_session() as s:
        s.execute(delete(RawSigetLinha).where(RawSigetLinha.source_file == src))
        s.bulk_insert_mappings(RawSigetLinha, rows)
    return len(rows)


if __name__ == "__main__":
    print("raw_siget_linha:", ingest_raw_siget_linha())
