"""Inspect SIGET — Contrato Módulo Linha Transmissão.

Cadastro da rede básica (linhas ativas e desativadas). Dá topologia
(subestação-subestação), tensão e extensão. Não dá MVA nem impedância.
"""
from __future__ import annotations

import pandas as pd

PATH = (
    "datasets/SIGET - Contrato Módulo Linha Transmissão/"
    "siget-contrato-modulolinhatransmissao-subestacaoorigem-subestacaodestino.csv"
)

UF_TO_SUB = {}
for uf in "MG ES RJ SP GO MT MS DF AC RO".split():
    UF_TO_SUB[uf] = "SE/CO"
for uf in "PR SC RS".split():
    UF_TO_SUB[uf] = "S"
for uf in "BA SE AL PE PB RN CE PI MA".split():
    UF_TO_SUB[uf] = "NE"
for uf in "PA AP AM RR TO".split():
    UF_TO_SUB[uf] = "N"


def load() -> pd.DataFrame:
    df = pd.read_csv(PATH, sep=";", encoding="latin1", low_memory=False)
    df["km"] = pd.to_numeric(
        df["NumEtnLinTms"].astype(str).str.replace(",", ".", regex=False), errors="coerce"
    )
    df["kV"] = pd.to_numeric(
        df["NumTensaoBaseLinhaTransm"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )
    df["sub_o"] = df["SigUFSubestacaoOrigem"].map(UF_TO_SUB)
    df["sub_d"] = df["SigUFSubestacaoDestino"].map(UF_TO_SUB)
    return df


def main() -> None:
    pd.set_option("display.max_columns", 40)
    pd.set_option("display.width", 240)

    df = load()
    print("shape:", df.shape)
    print("situação:", df["DscSitLinTms"].value_counts().to_dict())
    print()

    print("linhas × tensão (kV) — resumo:")
    g = (
        df[df["DscSitLinTms"] == "Ativa"]
        .groupby("kV")["km"]
        .agg(["count", "sum", "mean", "median"])
        .round(1)
    )
    print(g)
    print()

    print("fluxo entre subsistemas (n linhas ativas):")
    at = df[df["DscSitLinTms"] == "Ativa"]
    print(pd.crosstab(at["sub_o"], at["sub_d"]))
    print()

    inter = at[at["sub_o"] != at["sub_d"]].copy()
    inter["par"] = inter.apply(
        lambda r: tuple(sorted([r["sub_o"], r["sub_d"]])), axis=1
    )
    print("km por par inter-subsistema × tensão:")
    print(
        inter.groupby(["par", "kV"])["km"].agg(["count", "sum"]).round(0)
    )


if __name__ == "__main__":
    main()
