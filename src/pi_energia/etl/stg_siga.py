"""RAW SIGA → DimUsinaSiga."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import delete, select

from pi_energia.config import UF_TO_SUB
from pi_energia.db.engine import get_engine
from pi_energia.db.models import DimSubsistema, DimUsinaSiga
from pi_energia.db.session import db_session


def build_stg_siga() -> dict[str, int]:
    engine = get_engine()
    df = pd.read_sql_query(
        """
        SELECT CodCEG, SigUFPrincipal, DscFaseUsina,
               MdaPotenciaOutorgadaKw, MdaPotenciaFiscalizadaKw,
               MdaGarantiaFisicaKw,
               NumCoordNEmpreendimento AS lat,
               NumCoordEEmpreendimento AS lon
        FROM raw_siga_usina
        """,
        engine,
    )
    df["sub_sigla"] = df["SigUFPrincipal"].map(UF_TO_SUB)
    df = df.dropna(subset=["sub_sigla"]).reset_index(drop=True)

    with db_session() as s:
        sig_to_id = {
            d.sigla: d.id_subsistema
            for d in s.execute(select(DimSubsistema)).scalars()
        }

        s.execute(delete(DimUsinaSiga))
        s.flush()
        usinas = []
        for r in df.itertuples(index=False):
            usinas.append(
                {
                    "CodCEG": r.CodCEG,
                    "id_subsistema": sig_to_id[r.sub_sigla],
                    "uf": r.SigUFPrincipal,
                    "fase": r.DscFaseUsina,
                    "mw_outorgada": (r.MdaPotenciaOutorgadaKw / 1000.0) if pd.notna(r.MdaPotenciaOutorgadaKw) else None,
                    "mw_fiscalizada": (r.MdaPotenciaFiscalizadaKw / 1000.0) if pd.notna(r.MdaPotenciaFiscalizadaKw) else None,
                    "mw_garantia_fisica": (r.MdaGarantiaFisicaKw / 1000.0) if pd.notna(r.MdaGarantiaFisicaKw) else None,
                    "lat": r.lat if pd.notna(r.lat) else None,
                    "lon": r.lon if pd.notna(r.lon) else None,
                }
            )
        batch = 2000
        for i in range(0, len(usinas), batch):
            s.bulk_insert_mappings(DimUsinaSiga, usinas[i : i + batch])

        return {"dim_usina_siga": len(usinas)}


if __name__ == "__main__":
    print(build_stg_siga())
