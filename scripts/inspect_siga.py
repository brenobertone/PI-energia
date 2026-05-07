"""Inspect ANEEL SIGA — cadastro de empreendimentos de geração.

Encoding latin1; separador ';'; decimal vírgula nas colunas de potência e
coordenadas. Cada linha = uma unidade geradora (UFV, EOL, UHE, UTE, PCH, ...)
com fase (Operação / Construção / Construção não iniciada).
"""
from __future__ import annotations

import pandas as pd

PATH = "datasets/siga/siga-empreendimentos-geracao.csv"

# Mapeamento simplificado UF -> subsistema SIN (boa aproximação para modelos de
# 4 barras; sistemas isolados do Norte ficam fora do SIN no mundo real).
UF_TO_SUB = {}
for uf in "MG ES RJ SP GO MT MS DF AC RO".split():
    UF_TO_SUB[uf] = "SE/CO"
for uf in "PR SC RS".split():
    UF_TO_SUB[uf] = "S"
for uf in "BA SE AL PE PB RN CE PI MA".split():
    UF_TO_SUB[uf] = "NE"
for uf in "PA AP AM RR TO".split():
    UF_TO_SUB[uf] = "N"

TECH_FROM_TIPO = {
    "UFV": "Solar",
    "EOL": "Eólica",
    "UHE": "Hidro",
    "PCH": "PCH",
    "CGH": "CGH",
    "UTE": "Térmica",
    "UTN": "Nuclear",
}


def load() -> pd.DataFrame:
    df = pd.read_csv(PATH, sep=";", encoding="latin1", low_memory=False)
    for c in (
        "MdaPotenciaOutorgadaKw",
        "MdaPotenciaFiscalizadaKw",
        "MdaGarantiaFisicaKw",
        "NumCoordNEmpreendimento",
        "NumCoordEEmpreendimento",
    ):
        df[c] = pd.to_numeric(
            df[c].astype(str).str.replace(",", ".", regex=False), errors="coerce"
        )
    df["MW_outorgada"] = df["MdaPotenciaOutorgadaKw"] / 1000.0
    df["tech"] = df["SigTipoGeracao"].map(TECH_FROM_TIPO)
    df["subsis"] = df["SigUFPrincipal"].map(UF_TO_SUB)
    return df


def main() -> None:
    pd.set_option("display.max_columns", 40)
    pd.set_option("display.width", 220)

    df = load()
    print("n linhas:", len(df))
    print("colunas:", list(df.columns))
    print()
    print("Fases:", df["DscFaseUsina"].value_counts().to_dict())
    print("Tipos:", df["SigTipoGeracao"].value_counts().to_dict())
    print()

    print("GW por tecnologia × fase:")
    g = (
        df.groupby(["tech", "DscFaseUsina"])["MW_outorgada"]
        .sum()
        .unstack(fill_value=0)
        / 1000
    )
    print(g.round(2))
    print()

    print("GW em Operação por tecnologia × subsistema:")
    g = (
        df[df["DscFaseUsina"] == "Operação"]
        .groupby(["tech", "subsis"])["MW_outorgada"]
        .sum()
        .unstack(fill_value=0)
        / 1000
    )
    print(g.round(2))
    print()

    # Pipeline = construção + construção não iniciada (entrante até ~2028).
    pipe = df[df["DscFaseUsina"].isin(["Construção", "Construção não iniciada"])]
    print("Pipeline (GW) por tecnologia × subsistema:")
    g = (
        pipe.groupby(["tech", "subsis"])["MW_outorgada"]
        .sum()
        .unstack(fill_value=0)
        / 1000
    )
    print(g.round(2))


if __name__ == "__main__":
    main()
