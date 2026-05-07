"""View 4 — Rede de Transmissão (SIGET)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pi_energia.config import UF_TO_SUB
from pi_energia.viz.queries import ref_mva, siget_interligacao, siget_linhas_raw

SUB_ORDER = ["N", "NE", "S", "SE_CO"]
KV_PALETTE = {
    230: "#1565c0",
    345: "#1e88e5",
    440: "#26c6da",
    500: "#43a047",
    525: "#a5d6a7",
    600: "#fb8c00",
    800: "#e53935",
}


def _agregar_interligacao(linhas_raw: pd.DataFrame, mva_ref_df: pd.DataFrame) -> pd.DataFrame:
    """Agrega linhas individuais em MVA por (sub_origem, sub_destino, kV)."""
    mva_ref = {int(r["kV"]): (r["mva_ref"], r["fator_potencia"]) for _, r in mva_ref_df.iterrows()}
    df = linhas_raw.copy()
    df["sub_o"] = df["uf_orig"].map(UF_TO_SUB)
    df["sub_d"] = df["uf_dest"].map(UF_TO_SUB)
    df = df.dropna(subset=["sub_o", "sub_d", "kV"])
    inter = df[df["sub_o"] != df["sub_d"]].copy()
    inter["kV_int"] = inter["kV"].round().astype(int)
    inter["sub_origem"] = inter.apply(lambda r: min(r["sub_o"], r["sub_d"]), axis=1)
    inter["sub_destino"] = inter.apply(lambda r: max(r["sub_o"], r["sub_d"]), axis=1)
    agg = (
        inter.groupby(["sub_origem", "sub_destino", "kV_int"])
        .agg(n_circuitos=("kV_int", "count"), km_total=("km", "sum"))
        .reset_index()
        .rename(columns={"kV_int": "kV"})
    )
    rows = []
    for _, r in agg.iterrows():
        if int(r["kV"]) not in mva_ref:
            continue
        mva_unit, fp = mva_ref[int(r["kV"])]
        rows.append({
            "sub_origem": r["sub_origem"],
            "sub_destino": r["sub_destino"],
            "kV": int(r["kV"]),
            "n_circuitos": int(r["n_circuitos"]),
            "km_total": float(r["km_total"]) if pd.notna(r["km_total"]) else 0.0,
            "mva_total": float(r["n_circuitos"]) * float(mva_unit) * float(fp),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=300)
def _load():
    linhas_raw = siget_interligacao()
    mva_ref_df = ref_mva()
    interlig = _agregar_interligacao(linhas_raw, mva_ref_df)
    linhas = siget_linhas_raw()
    return interlig, linhas, mva_ref_df


def render():
    st.header("View 4 — Rede de Transmissão (SIGET)")
    st.caption(
        "Capacidade de intercâmbio entre subsistemas, derivada das linhas de transmissão do ONS. "
        "No modelo de otimização, esses valores definem os limites **f_barra** de fluxo máximo entre nós."
    )

    with st.expander("📖 Glossário desta view", expanded=False):
        st.markdown("""
| Termo | Significado |
|-------|-------------|
| **MVA (megavolt-ampere)** | Unidade de capacidade elétrica aparente. Difere do MW porque inclui potência reativa. Para fins do modelo, é tratado como proxy de MW com fator de potência ≈ 0,95. |
| **Intercâmbio / Interligação** | Fluxo de energia elétrica transferido de um subsistema para outro via linhas de transmissão inter-regionais. |
| **f_barra** | Parâmetro do modelo MILP: capacidade máxima de fluxo em cada arco (par de subsistemas). É calculado somando os MVA das linhas ativas entre os dois subsistemas. |
| **Par (subsistema A ↔ B)** | Combinação direcional de dois subsistemas ligados por linhas de transmissão. |
| **Circuito** | Conjunto de cabos condutores numa linha. Uma torre dupla-terna tem dois circuitos independentes. O número de circuitos multiplica a capacidade total da conexão. |
| **kV (kilovolt)** | Tensão de operação da linha. Linhas de maior tensão transportam mais energia e têm maior MVA unitário. |
| **MVA de referência** | Capacidade padrão assumida por circuito para cada nível de tensão (ex.: 500 kV → ~1.000 MVA por circuito). Multiplicado por fator de potência (≈ 0,95) para obter MW equivalente. |
| **Matriz 4×4** | Representa graficamente o fluxo máximo possível entre todos os pares de subsistemas. A diagonal é zero (sem autoloop). Assimetrias podem existir se as linhas forem unidirecionais. |
        """)

    interlig, linhas, mva_ref = _load()

    status_opts = linhas["DscSitLinTms"].dropna().unique().tolist()
    col1, col2 = st.columns(2)
    with col1:
        status_sel = st.multiselect(
            "Status da linha",
            status_opts,
            default=[s for s in ["Ativa"] if s in status_opts],
            help="Ativa = linha em operação comercial. Linhas em construção ou planejadas ainda não contribuem para a capacidade real.",
        )
    with col2:
        kv_opts = sorted(linhas["kv"].dropna().unique().astype(int).tolist())
        kv_sel = st.multiselect(
            "Nível de tensão (kV)",
            kv_opts,
            default=kv_opts,
            help="Kilovolt: tensão elétrica da linha. Apenas linhas de 230 kV ou mais integram a rede de transmissão básica do ONS.",
        )

    linhas_f = linhas.copy()
    if status_sel:
        linhas_f = linhas_f[linhas_f["DscSitLinTms"].isin(status_sel)]
    if kv_sel:
        linhas_f = linhas_f[linhas_f["kv"].isin(kv_sel)]

    interlig_f = interlig.copy()
    if kv_sel:
        interlig_f = interlig_f[interlig_f["kV"].isin(kv_sel)]

    # ── Barras empilhadas: MVA por par × kV ──────────────────────────────────
    st.subheader("Capacidade total de intercâmbio por par de subsistemas")
    st.caption("Cada barra empilhada soma os MVA de todos os circuitos ativos entre o par, separados por nível de tensão. O número dentro da barra é a quantidade de circuitos. Este total é o valor usado como f_barra no modelo.")

    interlig_f["par"] = interlig_f["sub_origem"] + " ↔ " + interlig_f["sub_destino"]
    interlig_f["kV_str"] = interlig_f["kV"].astype(str) + " kV"
    interlig_agg = (
        interlig_f.groupby(["par", "kV_str"], as_index=False)
        .agg(mva_total=("mva_total", "sum"), n_circuitos=("n_circuitos", "sum"))
    )

    fig_bar = px.bar(
        interlig_agg.sort_values("kV_str"),
        x="par", y="mva_total",
        color="kV_str",
        text="n_circuitos",
        barmode="stack",
        labels={"mva_total": "MVA total", "kV_str": "Tensão", "par": "Par"},
    )
    fig_bar.update_traces(textposition="inside", textfont_size=10)
    fig_bar.update_layout(height=360, margin=dict(t=10, b=0))
    st.plotly_chart(fig_bar, use_container_width=True)
    st.caption("Número dentro de cada barra = circuitos. Marcador na barra = capacidade somada no mart_arco.")

    # ── Matriz 4×4 ───────────────────────────────────────────────────────────
    st.subheader("Matriz de capacidade inter-subsistema (MVA total)")
    st.caption("Cada célula (linha A, coluna B) mostra o MVA total de linhas ativas entre os subsistemas A e B. A matriz é simetrizada: o modelo trata o intercâmbio como bidirecional com o mesmo limite em ambas as direções. Células em branco = sem ligação direta.")

    mat_data = (
        interlig_f.groupby(["sub_origem", "sub_destino"])["mva_total"]
        .sum()
        .reset_index()
    )
    # espelha para obter tabela simétrica
    mat_sym = pd.concat([
        mat_data,
        mat_data.rename(columns={"sub_origem": "sub_destino", "sub_destino": "sub_origem"}),
    ]).groupby(["sub_origem", "sub_destino"])["mva_total"].sum().reset_index()

    pivot = mat_sym.pivot(index="sub_origem", columns="sub_destino", values="mva_total").fillna(0)
    for s in SUB_ORDER:
        if s not in pivot.index:
            pivot.loc[s] = 0
        if s not in pivot.columns:
            pivot[s] = 0
    pivot = pivot.loc[SUB_ORDER, SUB_ORDER]
    # diagonal zero (sem loop)
    for s in SUB_ORDER:
        pivot.loc[s, s] = 0

    fig_mat = px.imshow(
        pivot,
        color_continuous_scale="Blues",
        text_auto=".0f",
        labels={"color": "MVA"},
        title="MVA total (linhas ativas)",
    )
    fig_mat.update_layout(height=340, margin=dict(t=40, b=0))
    st.plotly_chart(fig_mat, use_container_width=True)

    # ── Scatter km × kV ──────────────────────────────────────────────────────
    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Comprimento × tensão por linha")
        st.caption("Cada ponto é uma linha. Linhas de alta tensão (500+ kV) tendem a ser mais longas — são as conexões inter-regionais de longa distância. Passe o mouse para ver o nome e as UFs de origem e destino.")
        df_sc = linhas_f.dropna(subset=["km", "kv"]).copy()
        df_sc["kV_str"] = df_sc["kv"].astype(int).astype(str) + " kV"
        fig_sc = px.scatter(
            df_sc,
            x="km", y="kv",
            color="kV_str",
            opacity=0.55,
            hover_name="NomLinTms",
            hover_data={"uf_orig": True, "uf_dest": True, "DscSitLinTms": True},
            labels={"km": "Comprimento (km)", "kv": "Tensão (kV)"},
        )
        fig_sc.update_layout(height=340, margin=dict(t=10, b=0), showlegend=False)
        st.plotly_chart(fig_sc, use_container_width=True)

    with col_b:
        st.subheader("Histograma de comprimentos por tensão")
        st.caption("Distribuição do comprimento das linhas. Linhas de 138–230 kV são numerosas e curtas (distribuição regional). Linhas de 500+ kV são poucas e longas — são as \"autoestradas\" de energia do SIN.")
        fig_hist = px.histogram(
            df_sc,
            x="km", color="kV_str",
            nbins=50,
            labels={"km": "Comprimento (km)", "kV_str": "Tensão"},
        )
        fig_hist.update_layout(height=340, margin=dict(t=10, b=0))
        st.plotly_chart(fig_hist, use_container_width=True)

    # ── KPIs ─────────────────────────────────────────────────────────────────
    st.divider()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Linhas ativas", f"{len(linhas_f[linhas_f['DscSitLinTms']=='Ativa']):,}")
    k2.metric("km totais (ativas)", f"{linhas_f[linhas_f['DscSitLinTms']=='Ativa']['km'].sum():,.0f} km")
    k3.metric("MVA inter-regional total", f"{interlig_f['mva_total'].sum():,.0f} MVA")
    k4.metric("Pares com interligação", f"{interlig_f[['sub_origem','sub_destino']].drop_duplicates().shape[0]}")

    # ── Tabela ref MVA/kV ─────────────────────────────────────────────────────
    with st.expander("Tabela de referência MVA por nível de tensão (base de cálculo do f_barra)"):
        st.caption(
            "Para cada nível de tensão, define-se um MVA de referência por circuito e um fator de potência. "
            "O f_barra de um par de subsistemas é calculado como: Σ(n_circuitos × mva_ref × fator_potência) "
            "para todas as linhas ativas entre os dois subsistemas."
        )
        st.dataframe(mva_ref, use_container_width=True)
