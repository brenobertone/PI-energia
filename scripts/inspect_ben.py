"""Inspect EPE BEN (Balanço Energético Nacional) 2024.

Planilha com fluxos de energia (produção, importação, oferta, consumo,
perdas, etc.) em 10^3 tep por fonte. Formato wide, legível por humano.
"""
from __future__ import annotations

import pandas as pd

PATH = "datasets/balanco_energetico_nacional/Matriz ab2024.xlsx"


def main() -> None:
    pd.set_option("display.max_columns", 12)
    pd.set_option("display.width", 220)

    xl = pd.ExcelFile(PATH)
    print("abas:", xl.sheet_names)
    for s in xl.sheet_names:
        df = pd.read_excel(PATH, sheet_name=s, header=None)
        print(f"\n=== {s} === shape={df.shape}")
        print(df.head(15).to_string())


if __name__ == "__main__":
    main()
