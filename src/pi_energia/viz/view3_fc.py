"""View 3 — Perfis de Disponibilidade Renovável (FC ONS)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pi_energia.viz.queries import fc_horario_raw, fc_por_usina

SUB_ORDER = ["N", "NE", "S", "SE_CO"]
TECH_COLOR = {"sol": "#f7d24f", "eol": "#4fcff7"}
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def _fc_ponderado_subsistema(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Agrega FC por usina em FC ponderado por capacidade para cada (instante, subsistema, tecnologia)."""
    df_raw = df_raw.copy()
    df_raw["fc_x_mw"] = df_raw["fc"] * df_raw["mw_instalado"]
    agg = (
        df_raw.groupby(["din_instante", "subsistema", "tecnologia"], as_index=False)
        .agg(fc_x_mw_sum=("fc_x_mw", "sum"), capacidade_total_mw=("mw_instalado", "sum"))
    )
    agg["fc"] = agg["fc_x_mw_sum"] / agg["capacidade_total_mw"]
    return agg.drop(columns="fc_x_mw_sum")


@st.cache_data(ttl=300)
def _load():
    df_raw = fc_horario_raw()
    df_raw["din_instante"] = pd.to_datetime(df_raw["din_instante"])
    df = _fc_ponderado_subsistema(df_raw)
    df["mes"] = df["din_instante"].dt.month
    df["hora"] = df["din_instante"].dt.hour
    df["mes_nome"] = df["mes"].apply(lambda m: MESES[m - 1])
    return df


@st.cache_data(ttl=300)
def _load_usinas():
    return fc_por_usina()


def _heatmap_mes_hora(df: pd.DataFrame, sub: str, tech: str, title: str):
    d = df[(df["subsistema"] == sub) & (df["tecnologia"] == tech)]
    if d.empty:
        return None
    pivot = d.groupby(["mes", "hora"])["fc"].mean().reset_index()
    mat = pivot.pivot(index="hora", columns="mes", values="fc")
    # garantir colunas 1..12
    for m in range(1, 13):
        if m not in mat.columns:
            mat[m] = np.nan
    mat = mat[sorted(mat.columns)]
    mat.columns = [MESES[c - 1] for c in mat.columns]

    fig = px.imshow(
        mat,
        color_continuous_scale="YlOrRd" if tech == "sol" else "Blues",
        zmin=0, zmax=1,
        aspect="auto",
        labels={"x": "Mês", "y": "Hora", "color": "FC"},
        title=title,
    )
    fig.update_layout(height=220, margin=dict(t=36, b=0, l=40, r=10))
    fig.update_yaxes(tickvals=list(range(0, 24, 4)))
    return fig


def render():
    st.header("View 3 — Perfis de Disponibilidade Renovável (Fator de Capacidade)")
    st.caption(
        "O Fator de Capacidade (FC) mede quanto de sua capacidade nominal uma usina efetivamente gerou num dado período. "
        "É o parâmetro central do modelo: define o quanto de energia cada MW instalado entrega hora a hora."
    )

    with st.expander("📖 Glossário desta view", expanded=False):
        st.markdown("""
| Termo | Significado |
|-------|-------------|
| **FC (Fator de Capacidade)** | FC = geração real ÷ geração máxima possível. FC=1 significa usina gerando 100% da capacidade; FC=0,25 significa 25%. Solar tem FC=0 à noite e próximo de 1 ao meio-dia. |
| **FC ponderado** | FC médio ponderado pela capacidade instalada de cada usina no subsistema. Representa o perfil típico de geração daquele grupo. Calculado a partir dos dados individuais por usina (RAW). |
| **Heatmap hora × mês** | Matriz onde cada célula mostra o FC médio para aquela combinação de hora do dia e mês do ano. Revela sazonalidade (variação anual) e perfil diário ao mesmo tempo. |
| **Curva de Duração (CDG)** | Os valores de FC são ordenados do maior para o menor e plotados. O eixo X mostra "em que % das horas do ano o FC foi igual ou maior que este valor". Útil para entender quantas horas a usina opera acima de certo limiar. |
| **FC=0,20 (linha de referência)** | Valor de corte comum: usinas com FC médio abaixo de 0,20 contribuem pouco para a capacidade firme do sistema. |
| **Correlação cruzada entre subsistemas** | Mede se o vento sopra (ou o sol brilha) ao mesmo tempo em regiões diferentes. Baixa correlação entre NE e S, por exemplo, é positiva: quando um cai, o outro pode compensar. |
| **FC médio anual por conjunto** | Desempenho histórico de cada parque eólico ou solar específico no período disponível. |
        """)

    df = _load()

    if df.empty:
        st.warning("Tabela raw_fator_capacidade vazia. Execute `pi ingest` primeiro.")
        return

    techs = [t for t in ["sol", "eol"] if t in df["tecnologia"].unique()]
    subs_disp = [s for s in SUB_ORDER if s in df["subsistema"].unique()]

    # ── Heatmaps mês × hora ──────────────────────────────────────────────────
    for tech in techs:
        st.subheader(f"{'Solar' if tech == 'sol' else 'Eólico'} — FC médio por hora do dia × mês do ano")
        st.caption(
            "Cada célula é a média do FC naquela hora e mês. "
            + ("Solar: FC=0 antes do nascer e após o pôr do sol; pico ao meio-dia. Sazonalidade reflete irradiação ao longo do ano." if tech == "sol"
               else "Eólico: sem padrão diário fixo, mas com sazonalidade: ventos mais intensos em certos meses (ex.: NE mais forte no 2º semestre).")
        )
        cols = st.columns(len(subs_disp))
        for i, sub in enumerate(subs_disp):
            fig = _heatmap_mes_hora(df, sub, tech, sub)
            if fig:
                cols[i].plotly_chart(fig, use_container_width=True)
            else:
                cols[i].caption(f"{sub} — sem dados (proxy no mart)")

    # ── Série horária completa ────────────────────────────────────────────────
    st.divider()
    st.subheader("Série horária de FC — 2025")
    st.caption("FC ponderado pela capacidade instalada, hora a hora, para o subsistema e tecnologia selecionados.")

    col1, col2 = st.columns(2)
    with col1:
        sub_sel = st.selectbox("Subsistema", subs_disp, key="fc_sub")
    with col2:
        tech_sel = st.selectbox("Tecnologia", techs, key="fc_tech")

    d_serie = (
        df[(df["subsistema"] == sub_sel) & (df["tecnologia"] == tech_sel)]
        .sort_values("din_instante")
    )

    if not d_serie.empty:
        # banda min-max por hora do dia dentro de cada mês
        banda = (
            df[(df["subsistema"] == sub_sel) & (df["tecnologia"] == tech_sel)]
            .groupby(["mes", "hora"])["fc"]
            .agg(["min", "max"])
            .reset_index()
        )
        fig_serie = go.Figure()
        fig_serie.add_trace(go.Scatter(
            x=d_serie["din_instante"], y=d_serie["fc"],
            mode="lines", name="FC ponderado",
            line=dict(color=TECH_COLOR.get(tech_sel, "#aaa"), width=0.8),
        ))
        fig_serie.update_layout(
            height=280,
            xaxis_title="", yaxis_title="FC",
            margin=dict(t=10, b=0),
            yaxis=dict(range=[0, 1]),
            hovermode="x",
        )
        st.plotly_chart(fig_serie, use_container_width=True)

    # ── Curva de duração ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("Curva de Duração do Fator de Capacidade (CDG)")
    st.caption(
        "Os valores horários de FC são ordenados do maior para o menor e plotados contra o percentual de horas do ano. "
        "Leitura: no ponto (20%, 0,8) a usina operou com FC ≥ 0,8 em 20% das horas. "
        "A área sob a curva é proporcional ao FC médio anual. "
        "A linha tracejada em FC=0,20 é um limiar de referência abaixo do qual a contribuição para a capacidade firme é baixa."
    )

    fig_cdg = go.Figure()
    for sub in subs_disp:
        for tech in techs:
            d = df[(df["subsistema"] == sub) & (df["tecnologia"] == tech)]["fc"].dropna()
            if d.empty:
                continue
            sorted_fc = np.sort(d.values)[::-1]
            pct = np.linspace(0, 100, len(sorted_fc))
            color = TECH_COLOR.get(tech, "#aaa")
            dash = "solid" if tech == "sol" else "dash"
            fig_cdg.add_trace(go.Scatter(
                x=pct, y=sorted_fc,
                mode="lines",
                name=f"{sub} {tech}",
                line=dict(color=color, width=1.2, dash=dash),
            ))

    fig_cdg.add_hline(y=0.20, line_dash="dot", line_color="gray",
                      annotation_text="FC=0.20", annotation_position="right")
    fig_cdg.update_layout(
        height=320,
        xaxis_title="% das horas do ano",
        yaxis_title="FC",
        yaxis=dict(range=[0, 1]),
        legend=dict(orientation="h", y=1.05),
        margin=dict(t=10, b=0),
    )
    st.plotly_chart(fig_cdg, use_container_width=True)

    # ── Correlação cruzada entre subsistemas ─────────────────────────────────
    st.divider()
    st.subheader("Correlação do FC eólico entre pares de subsistemas")
    st.caption(
        "Cada ponto é uma hora do ano. r próximo de 0 indica que os ventos nos dois subsistemas são independentes — "
        "boa notícia para o sistema, pois quando um subsistema tem vento fraco o outro pode compensar. "
        "r alto indica que os sistemas caem juntos, aumentando o risco de déficit simultâneo."
    )

    if "eol" in techs and len(subs_disp) >= 2:
        df_eol = df[df["tecnologia"] == "eol"].copy()
        df_eol_wide = df_eol.pivot_table(
            index="din_instante", columns="subsistema", values="fc"
        ).dropna(how="all")

        subs_eol = [s for s in SUB_ORDER if s in df_eol_wide.columns]
        pairs = [(a, b) for i, a in enumerate(subs_eol) for b in subs_eol[i + 1:]]

        if pairs:
            cols = st.columns(min(len(pairs), 3))
            for idx, (a, b) in enumerate(pairs[:3]):
                dxy = df_eol_wide[[a, b]].dropna()
                r = np.corrcoef(dxy[a], dxy[b])[0, 1] if len(dxy) > 1 else 0
                # amostra para não sobrecarregar o browser
                sample = dxy.sample(min(len(dxy), 2000), random_state=42)
                fig_sc = px.scatter(
                    sample, x=a, y=b,
                    opacity=0.3,
                    color_discrete_sequence=["#4fcff7"],
                    labels={a: f"FC eol {a}", b: f"FC eol {b}"},
                    title=f"{a} × {b}  r={r:.2f}",
                )
                fig_sc.update_layout(height=280, margin=dict(t=40, b=0))
                cols[idx].plotly_chart(fig_sc, use_container_width=True)

    # ── FC por usina (raw) ────────────────────────────────────────────────────
    st.divider()
    st.subheader("FC médio anual por parque (dados brutos ONS)")
    st.caption(
        "Ranking dos parques eólicos ou solares pelo seu FC médio histórico. "
        "\"Conjunto\" é o nome operacional do parque no ONS (pode agrupar várias usinas físicas). "
        "Parques com FC alto são os mais eficientes — geram mais energia por MW instalado. "
        "Esses valores informam a calibração do parâmetro `alpha` por usina no modelo."
    )

    df_usinas = _load_usinas()
    if df_usinas.empty:
        st.info("Tabela raw_fator_capacidade não carregada.")
        return

    tech_map = {"Eólica": "eol", "Solar": "sol"}
    df_usinas["tecnologia"] = df_usinas["tipo_ons"].map(tech_map).fillna(df_usinas["tipo_ons"])

    col1, col2 = st.columns(2)
    with col1:
        tech_u = st.selectbox("Tecnologia (usinas)", ["eol", "sol"], key="u_tech")
    with col2:
        top_n = st.slider("Top N usinas", 20, 200, 50, step=10)

    df_u = df_usinas[df_usinas["tecnologia"] == tech_u].nlargest(top_n, "fc_medio")
    fig_rank = px.bar(
        df_u.sort_values("fc_medio"),
        x="fc_medio", y="nom_usina_conjunto",
        orientation="h",
        color="fc_medio",
        color_continuous_scale="YlOrRd" if tech_u == "sol" else "Blues",
        hover_data={"mw_instalado": ":.1f", "n_horas": True},
        labels={"fc_medio": "FC médio anual", "nom_usina_conjunto": "Conjunto"},
    )
    fig_rank.update_layout(
        height=max(300, top_n * 14),
        margin=dict(t=10, b=0, l=10, r=10),
        yaxis=dict(tickfont=dict(size=10)),
        showlegend=False,
    )
    st.plotly_chart(fig_rank, use_container_width=True)
