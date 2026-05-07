"""Ingestão da tabela MVA-por-kV (hipótese MVP)."""
from __future__ import annotations

import yaml
from sqlalchemy import delete

from pi_energia.config import REF_MVA_YML
from pi_energia.db.models import RawRefMvaPorTensao
from pi_energia.db.session import db_session


def ingest_raw_ref_mva() -> int:
    with REF_MVA_YML.open() as fh:
        data = yaml.safe_load(fh)
    fp = float(data.get("fator_potencia", 0.95))
    src = data.get("source", "hipótese MVP")
    rows = [
        {"kV": int(kv), "mva_ref": float(mva), "fator_potencia": fp, "fonte": src}
        for kv, mva in data["ref"].items()
    ]
    with db_session() as s:
        s.execute(delete(RawRefMvaPorTensao))
        s.bulk_insert_mappings(RawRefMvaPorTensao, rows)
    return len(rows)


if __name__ == "__main__":
    print("raw_ref_mva:", ingest_raw_ref_mva())
