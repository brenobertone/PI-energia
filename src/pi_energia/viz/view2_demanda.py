"""View 2 — Curvas de Demanda (Carga ONS)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pi_energia.viz.queries import carga_horaria

SUB_COLOR = {"N": "#4fcff7", "NE": "#f7d24f", "S": "#4ff7a2", "SE_CO": "#f7744f"}


@st.cache_data(ttl=300)
def _load() -> pd.DataFrame:
    df = carga_horaria()
    df["din_instante"] = pd.to_datetime(df["din_instante"])
    df["data"] = df["din_instante"].dt.normalize()
    df = df.groupby(["data", "subsistema"], as_index=False)["mwmed"].mean()
    df["mes"] = df["data"].dt.month
    df["dia_semana"] = df["data"].dt.day_name()
    return df


def render():
    st.header("View 2 — Curvas de Demanda")
    st.caption(
        "Carga elétrica observada em 2025 por subsistema, medida em MWmed (média diária). "
        "No modelo de otimização, a demanda é o parâmetro de entrada que cada subsistema precisa atender em cada período."
    )

    with st.expander("📖 Glossário desta view", expanded=False):
        st.markdown("""
| Termo | Significado |
|-------|-------------|
| **MWmed** | Megawatt médio — energia consumida num intervalo de tempo dividida pela duração desse intervalo. Um dia com MWmed = 1.000 consumiu 24.000 MWh de energia. |
| **Carga / Demanda** | Potência elétrica requerida pelos consumidores num dado instante. É a variável que o sistema de geração precisa atender. |
| **Subsistema (N, NE, S, SE_CO)** | Divisão elétrico-geográfica do SIN. Cada subsistema tem balanço próprio; excedentes ou déficits são trocados via linhas de interligação. |
| **Sazonalidade** | Variação sistemática da demanda ao longo do ano (ex.: verão mais quente → mais ar-condicionado → maior carga no SE_CO). |
| **Média mensal** | Valor médio da carga dentro do mês, calculado agrupando as leituras horárias por dia. |
| **Box-plot** | Cada caixa mostra a distribuição dos valores diários no mês: a linha central é a mediana, a caixa vai do 1º ao 3º quartil, os bigodes cobrem o restante. |
| **R²** | Coeficiente de determinação — mede o quanto a variação de demanda de um subsistema explica a variação de outro (0 = nenhuma relação, 1 = perfeitamente correlacionados). |
        """)

    df = _load()

    subs = st.multiselect(
        "Subsistemas", ["N", "NE", "S", "SE_CO"], default=["N", "NE", "S", "SE_CO"],
        help="N=Norte, NE=Nordeste, S=Sul, SE_CO=Sudeste/Centro-Oeste.",
    )
    df = df[df["subsistema"].isin(subs)]

    # ── Série temporal ────────────────────────────────────────────────────────
    st.subheader("Série temporal de carga diária — 2025")

    media_mensal = (
        df.groupby(["subsistema", "mes"], as_index=False)["mwmed"]
        .mean()
        .rename(columns={"mwmed": "media_mensal"})
    )
    df_plot = df.merge(media_mensal, on=["subsistema", "mes"])

    fig_serie = go.Figure()
    for sub in subs:
        d = df_plot[df_plot["subsistema"] == sub].sort_values("data")
        color = SUB_COLOR.get(sub, "#aaa")
        fig_serie.add_trace(go.Scatter(
            x=d["data"], y=d["mwmed"],
            mode="lines", name=sub,
            line=dict(color=color, width=1),
            hovertemplate=f"<b>{sub}</b> %{{x|%d/%m}}: %{{y:,.0f}} MWmed<extra></extra>",
        ))
        # média mensal como traço pontilhado
        fig_serie.add_trace(go.Scatter(
            x=d["data"], y=d["media_mensal"],
            mode="lines", name=f"{sub} média mensal",
            line=dict(color=color, width=1.5, dash="dot"),
            showlegend=False,
            hoverinfo="skip",
        ))

    fig_serie.update_layout(
        height=340,
        xaxis_title="", yaxis_title="MWmed",
        legend=dict(orientation="h", y=1.08),
        margin=dict(t=10, b=0),
        hovermode="x unified",
    )
    st.plotly_chart(fig_serie, use_container_width=True)
    st.caption(
        "Linha sólida = carga diária (MWmed, média das horas do dia) · "
        "Linha pontilhada = média mensal do mesmo subsistema. "
        "Quanto mais a linha sólida oscilar ao redor da pontilhada, maior a variabilidade intra-mensal."
    )

    # ── Box-plot mensal ───────────────────────────────────────────────────────
    st.subheader("Dispersão diária da carga dentro de cada mês")

    MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    df["mes_nome"] = df["mes"].apply(lambda m: MESES[m - 1])

    fig_box = px.box(
        df,
        x="mes_nome", y="mwmed",
        color="subsistema",
        color_discrete_map=SUB_COLOR,
        category_orders={"mes_nome": MESES, "subsistema": subs},
        labels={"mes_nome": "Mês", "mwmed": "MWmed", "subsistema": "Subsistema"},
        points=False,
    )
    fig_box.update_layout(height=360, margin=dict(t=10, b=0), boxgap=0.3)
    st.plotly_chart(fig_box, use_container_width=True)
    st.caption(
        "Cada caixa reúne os valores diários de carga de um subsistema num dado mês. "
        "A linha central é a mediana; a caixa cobre o intervalo interquartil (IQR = P75 − P25). "
        "Uma caixa larga significa que a demanda varia muito dentro do mês."
    )

    # ── Heatmap calendário ────────────────────────────────────────────────────
    st.subheader("Heatmap: padrão semanal de carga ao longo do ano")
    st.caption("Eixo X = semana do ano; Eixo Y = dia da semana (0=Segunda … 6=Domingo). Cor mais escura = maior carga média. Permite identificar padrões como fins de semana com carga menor e semanas de verão mais intensas.")

    col_sub = st.selectbox("Subsistema para heatmap", subs, index=min(3, len(subs) - 1))
    df_hm = df[df["subsistema"] == col_sub].copy()
    df_hm["semana_ano"] = df_hm["data"].dt.isocalendar().week.astype(int)
    df_hm["dia_semana_n"] = df_hm["data"].dt.dayofweek

    fig_hm = px.density_heatmap(
        df_hm,
        x="semana_ano", y="dia_semana_n",
        z="mwmed",
        histfunc="avg",
        color_continuous_scale="RdYlGn_r",
        labels={"semana_ano": "Semana do ano", "dia_semana_n": "Dia (0=Seg)", "mwmed": "MWmed"},
        title=f"Subsistema {col_sub} — carga média por semana × dia da semana",
    )
    fig_hm.update_layout(height=280, margin=dict(t=40, b=0))
    st.plotly_chart(fig_hm, use_container_width=True)

    # ── Correlação entre subsistemas ─────────────────────────────────────────
    if len(subs) >= 2:
        st.subheader("Correlação de demanda entre pares de subsistemas")
        st.caption(
            "Cada ponto é um dia. Subsistemas muito correlacionados (R² → 1) tendem a ter pico e vale no mesmo dia, "
            "dificultando o uso de intercâmbio como buffer. Subsistemas pouco correlacionados permitem compensação mútua."
        )
        df_wide = df.pivot_table(index="data", columns="subsistema", values="mwmed")
        df_wide = df_wide[[s for s in ["N", "NE", "S", "SE_CO"] if s in df_wide.columns]]

        pairs = [(a, b) for i, a in enumerate(df_wide.columns) for b in list(df_wide.columns)[i + 1:]]
        if pairs:
            n_cols = min(len(pairs), 3)
            cols = st.columns(n_cols)
            for idx, (a, b) in enumerate(pairs[:n_cols]):
                dxy = df_wide[[a, b]].dropna()
                r = np.corrcoef(dxy[a], dxy[b])[0, 1]
                fig_sc = px.scatter(
                    dxy, x=a, y=b,
                    opacity=0.5,
                    color_discrete_sequence=[SUB_COLOR.get(a, "#aaa")],
                    labels={a: f"{a} (MWmed)", b: f"{b} (MWmed)"},
                    title=f"{a} × {b}  (R²={r**2:.2f})",
                )
                m, c = np.polyfit(dxy[a], dxy[b], 1)
                x_range = [dxy[a].min(), dxy[a].max()]
                fig_sc.add_trace(go.Scatter(
                    x=x_range,
                    y=[m * x + c for x in x_range],
                    mode="lines",
                    line=dict(color="white", width=1.5, dash="dash"),
                    showlegend=False,
                ))
                fig_sc.update_layout(height=280, margin=dict(t=40, b=0))
                cols[idx].plotly_chart(fig_sc, use_container_width=True)
