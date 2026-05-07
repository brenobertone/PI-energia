"""Inspect ONS hourly capacity-factor dataset (FATOR_CAPACIDADE-2_*.parquet).

Por conjunto/usina (CEG), dá geração verificada, capacidade instalada e
fator de capacidade em passo horário. Cobertura: eólica (NE, S, poucas em N)
e solar (NE, SE/CO).
"""
from __future__ import annotations

import glob

import pandas as pd

GLOB = "datasets/fator_capacidade_eolica_solar/FATOR_CAPACIDADE*.parquet"


def load_all() -> pd.DataFrame:
    files = sorted(glob.glob(GLOB))
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    for c in ("val_fatorcapacidade", "val_capacidadeinstalada", "val_geracaoverificada"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def main() -> None:
    pd.set_option("display.max_columns", 40)
    pd.set_option("display.width", 240)

    df = load_all()
    print("shape:", df.shape)
    print("período:", df["din_instante"].min(), "→", df["din_instante"].max())
    print("n timestamps:", df["din_instante"].nunique())
    print("n usinas/conjuntos:", df["nom_usina_conjunto"].nunique())
    print()
    print("Tecnologias:", df["nom_tipousina"].value_counts().to_dict())
    print("Subsistemas:", df["nom_subsistema"].value_counts().to_dict())
    print()

    # Capacity-weighted FC per (subsystem, tech, hour).
    df["gen"] = df["val_capacidadeinstalada"] * df["val_fatorcapacidade"]
    agg = (
        df.groupby(["nom_subsistema", "nom_tipousina", "din_instante"])
        .agg(gen=("gen", "sum"), cap=("val_capacidadeinstalada", "sum"))
        .reset_index()
    )
    agg["fc"] = agg["gen"] / agg["cap"]

    print("FC anual ponderado por subsistema × tecnologia:")
    print(
        agg.groupby(["nom_subsistema", "nom_tipousina"])["fc"]
        .mean()
        .unstack()
        .round(3)
    )
    print()

    print("Perfil diário médio (Eólica Nordeste, FC ponderado):")
    ne = agg[(agg["nom_subsistema"] == "Nordeste") & (agg["nom_tipousina"] == "Eólica")].copy()
    ne["hora"] = ne["din_instante"].dt.hour
    print(ne.groupby("hora")["fc"].mean().round(3).to_string())


if __name__ == "__main__":
    main()
