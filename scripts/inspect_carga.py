"""Inspect ONS daily load-energy dataset (carga_energia).

Fonte: ONS, arquivo CARGA_ENERGIA_<ano>.parquet — carga de energia diária
(MWmed) agregada por subsistema.
"""
from __future__ import annotations

import pandas as pd

PATH = "datasets/carga_energia/CARGA_ENERGIA_2025.parquet"


def main() -> None:
    pd.set_option("display.max_columns", 40)
    pd.set_option("display.width", 220)

    df = pd.read_parquet(PATH)
    print("shape:", df.shape)
    print("dtypes:")
    print(df.dtypes, end="\n\n")
    print("head:")
    print(df.head(), end="\n\n")
    print("describe:")
    print(df.describe(include="all"), end="\n\n")

    # Temporal resolution (days between consecutive timestamps within a single subsystem).
    t = (
        df[df["id_subsistema"] == df["id_subsistema"].iloc[0]]
        .sort_values("din_instante")["din_instante"]
    )
    print("time step within a subsystem:", t.diff().dropna().iloc[0])

    print("\nn_dias =", df["din_instante"].nunique())
    print("subsistemas =", df["nom_subsistema"].unique())

    # Mean daily load per subsystem (MWmed).
    print("\nCarga média diária por subsistema (MWmed):")
    print(
        df.groupby(["id_subsistema", "nom_subsistema"])["val_cargaenergiamwmed"]
        .mean()
        .round(0)
    )

    # Seasonality: monthly average (good sanity check before using as demand proxy).
    df["mes"] = df["din_instante"].dt.month
    print("\nCarga média por mês × subsistema (MWmed):")
    print(
        df.groupby(["mes", "nom_subsistema"])["val_cargaenergiamwmed"]
        .mean()
        .unstack()
        .round(0)
    )


if __name__ == "__main__":
    main()
