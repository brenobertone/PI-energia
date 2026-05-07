"""Ingestão dos custos PDE 2035 transcritos em YAML."""
from __future__ import annotations

import yaml
from sqlalchemy import delete

from pi_energia.config import PDE_CUSTOS_YML
from pi_energia.db.models import RawPdeParametro
from pi_energia.db.session import db_session


def ingest_raw_pde() -> int:
    with PDE_CUSTOS_YML.open() as fh:
        data = yaml.safe_load(fh)
    src = data["meta"]["source"]
    rows = []
    for tech, params in data["tecnologias"].items():
        rows.append(
            {
                "tecnologia": tech,
                "variante": "ref",
                "nome": params.get("nome"),
                "capex_rs_kw": params.get("capex_rs_kw"),
                "om_fixo_rs_kw_ano": params.get("om_fixo_rs_kw_ano"),
                "cvu_rs_mwh": params.get("cvu_rs_mwh"),
                "vida_anos": params.get("vida_anos"),
                "bloco_mw": params.get("bloco_mw"),
                "is_expansivel": bool(params.get("is_expansivel", False)),
                "source_ref": src,
            }
        )
    with db_session() as s:
        s.execute(delete(RawPdeParametro))
        s.bulk_insert_mappings(RawPdeParametro, rows)
    return len(rows)


if __name__ == "__main__":
    print("raw_pde_parametro:", ingest_raw_pde())
