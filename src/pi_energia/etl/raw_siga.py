"""Ingestão ANEEL SIGA — cadastro de empreendimentos de geração."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import delete

from pi_energia.config import SIGA_CSV
from pi_energia.db.models import RawSigaUsina
from pi_energia.db.session import db_session

NUMERIC_COLS = [
    "MdaPotenciaOutorgadaKw",
    "MdaPotenciaFiscalizadaKw",
    "MdaGarantiaFisicaKw",
    "NumCoordNEmpreendimento",
    "NumCoordEEmpreendimento",
]


def _to_num(x):
    if x is None or pd.isna(x):
        return None
    s = str(x).replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def ingest_raw_siga() -> int:
    df = pd.read_csv(SIGA_CSV, sep=";", encoding="latin1", low_memory=False)
    # O CSV traz 3 duplicatas de CodCEG (registros idênticos). Mantemos 1.
    df = df.drop_duplicates(subset="CodCEG", keep="first").reset_index(drop=True)
    for c in NUMERIC_COLS:
        df[c] = df[c].map(_to_num)
    src = SIGA_CSV.name
    cols_keep = [
        "CodCEG",
        "NomEmpreendimento",
        "SigUFPrincipal",
        "SigTipoGeracao",
        "DscFaseUsina",
        "DscOrigemCombustivel",
        "DscFonteCombustivel",
        "NomFonteCombustivel",
        "DatEntradaOperacao",
        "MdaPotenciaOutorgadaKw",
        "MdaPotenciaFiscalizadaKw",
        "MdaGarantiaFisicaKw",
        "NumCoordNEmpreendimento",
        "NumCoordEEmpreendimento",
        "DscSubBacia",
        "DscMuninicpios",
    ]
    rows = []
    for r in df[cols_keep].itertuples(index=False):
        d = {c: getattr(r, c) for c in cols_keep}
        # limpar NaN string
        for k, v in list(d.items()):
            if isinstance(v, float) and pd.isna(v):
                d[k] = None
        d["source_file"] = src
        rows.append(d)
    with db_session() as s:
        s.execute(delete(RawSigaUsina).where(RawSigaUsina.source_file == src))
        s.bulk_insert_mappings(RawSigaUsina, rows)
    return len(rows)


if __name__ == "__main__":
    print("raw_siga_usina:", ingest_raw_siga())
