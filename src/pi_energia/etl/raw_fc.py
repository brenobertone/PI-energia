"""Ingestão ONS — fator de capacidade horário (eólica/solar)."""
from __future__ import annotations

import glob

import pandas as pd
from sqlalchemy import delete

from pi_energia.config import FC_DIR
from pi_energia.db.models import RawFatorCapacidade
from pi_energia.db.session import db_session

COLS_KEEP = [
    "id_subsistema",
    "nom_subsistema",
    "id_estado",
    "nom_estado",
    "cod_pontoconexao",
    "nom_tipousina",
    "nom_usina_conjunto",
    "ceg",
    "din_instante",
    "val_capacidadeinstalada",
    "val_geracaoverificada",
    "val_fatorcapacidade",
]


def ingest_raw_fc() -> int:
    files = sorted(glob.glob(str(FC_DIR / "FATOR_CAPACIDADE*.parquet")))
    total = 0
    with db_session() as s:
        for path in files:
            df = pd.read_parquet(path)
            for c in ("val_capacidadeinstalada", "val_geracaoverificada", "val_fatorcapacidade"):
                df[c] = pd.to_numeric(df[c], errors="coerce")
            # O ONS ocasionalmente emite duas linhas para o mesmo
            # (conjunto, ponto_conexao, instante) — uma delas com id_ons
            # placeholder e val_capacidadeinstalada vazia. Mantemos a
            # linha com capacidade não-nula (ou a última quando ambas nulas).
            df = (
                df.sort_values("val_capacidadeinstalada", na_position="first")
                .drop_duplicates(
                    subset=["nom_usina_conjunto", "cod_pontoconexao", "din_instante"],
                    keep="last",
                )
                .reset_index(drop=True)
            )
            src = path.rsplit("/", 1)[-1]
            s.execute(delete(RawFatorCapacidade).where(RawFatorCapacidade.source_file == src))
            rows = []
            for r in df[COLS_KEEP].itertuples(index=False):
                rows.append(
                    {
                        "id_subsistema": r.id_subsistema,
                        "nom_subsistema": r.nom_subsistema,
                        "id_estado": r.id_estado,
                        "nom_estado": r.nom_estado,
                        "cod_pontoconexao": r.cod_pontoconexao,
                        "nom_tipousina": r.nom_tipousina,
                        "nom_usina_conjunto": r.nom_usina_conjunto,
                        "ceg": r.ceg,
                        "din_instante": r.din_instante.to_pydatetime(),
                        "val_capacidadeinstalada": (
                            float(r.val_capacidadeinstalada)
                            if pd.notna(r.val_capacidadeinstalada) else None
                        ),
                        "val_geracaoverificada": (
                            float(r.val_geracaoverificada)
                            if pd.notna(r.val_geracaoverificada) else None
                        ),
                        "val_fatorcapacidade": (
                            float(r.val_fatorcapacidade)
                            if pd.notna(r.val_fatorcapacidade) else None
                        ),
                        "source_file": src,
                    }
                )
            s.bulk_insert_mappings(RawFatorCapacidade, rows)
            total += len(rows)
    return total


if __name__ == "__main__":
    print("raw_fator_capacidade:", ingest_raw_fc())
