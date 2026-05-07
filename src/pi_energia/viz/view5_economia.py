"""View 5 — Parâmetros Econômicos (PDE 2035)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pi_energia.viz.queries import pde_parametros, fc_horario_raw

TECH_COLOR = {"sol": "#f7d24f", "eol": "#4fcff7", "hidro": "#4f8ef7", "term": "#f7744f"}
TECH_LABEL = {"sol": "Solar", "eol": "Eólica", "hidro": "Hidro", "term": "Gás Natural"}


def _crf(wacc: float, n: float) -> float:
    if n <= 0:
        return 0.0
    return wacc * (1 + wacc) ** n / ((1 + wacc) ** n - 1)


@st.cache_data(ttl=300)
def _load():
    return pde_parametros()


@st.cache_data(ttl=300)
def _fc_medios() -> dict[tuple[str, str], float]:
    """FC médio anual ponderado por capacidade para cada (subsistema, tecnologia)."""
    try:
        df = fc_horario_raw()
        if df.empty:
            return {}
        df = df.copy()
        df["fc_x_mw"] = df["fc"] * df["mw_instalado"]
        agg = (
            df.groupby(["subsistema", "tecnologia"])
            .agg(fc_x_mw_sum=("fc_x_mw", "sum"), cap_sum=("mw_instalado", "sum"))
        )
        agg["fc"] = agg["fc_x_mw_sum"] / agg["cap_sum"]
        return agg["fc"].to_dict()
    except Exception:
        return {}


def render():
    st.header("View 5 — Parâmetros Econômicos (PDE 2035)")
    st.caption(
        "Custos de investimento e operação de cada tecnologia de geração, conforme o Plano Decenal de Expansão de Energia (PDE) 2035. "
        "Esses parâmetros alimentam a função objetivo do modelo de otimização."
    )

    with st.expander("📖 Glossário desta view", expanded=False):
        st.markdown("""
| Termo | Significado |
|-------|-------------|
| **CAPEX (R$/kW)** | Capital Expenditure — custo de investimento inicial para construir 1 kW de capacidade instalada. Ex.: R$ 3.500/kW para solar significa que uma usina de 100 MW custa ~R$ 350 milhões. |
| **OM fixo (R$/kW/ano)** | Operation & Maintenance — custo anual fixo de operação e manutenção, independente de quanto a usina gera. |
| **CVU (R$/MWh)** | Custo Variável Unitário — custo de cada MWh gerado (combustível, desgaste variável). Para renováveis é ~0; para gás é o maior componente variável. |
| **WACC (%)** | Weighted Average Cost of Capital — taxa de desconto que reflete o custo do capital (próprio + dívida). Quanto maior o WACC, mais caro é financiar projetos de longa maturação. |
| **CRF (Capital Recovery Factor)** | Fração do CAPEX que precisa ser recuperada a cada ano para amortizar o investimento ao longo da vida útil com o WACC definido. CRF = WACC × (1+WACC)ⁿ / ((1+WACC)ⁿ − 1). |
| **Vida útil (anos)** | Prazo contratual ou técnico de operação da usina — define por quantos anos o CAPEX é amortizado. |
| **LCOE (R$/MWh)** | Levelized Cost of Energy — custo nivelado de energia: quanto custa gerar 1 MWh ao longo de toda a vida do projeto, considerando CAPEX, OM e CVU. Fórmula: LCOE = (CAPEX × CRF + OM) / (FC × 8760 h/ano) + CVU. |
| **FC médio** | Fator de Capacidade médio anual usado no cálculo do LCOE. Calculado a partir dos dados históricos do ONS; caso indisponível usa default conservador. |
| **Horas equivalentes** | FC × 8760 — número de horas por ano em que a usina estaria gerando em plena capacidade para produzir a mesma energia. Uma solar com FC=0,22 tem ~1.927 horas equivalentes. |
| **Tecnologia expansível** | No modelo, tecnologia cujo bloco de capacidade pode ser ampliado (variável de decisão y ≥ 0). Geração existente (hidro) e nuclear são tratados como fixos. |
| **PDE 2035** | Plano Decenal de Expansão de Energia — documento do governo que projeta a expansão do sistema elétrico para os próximos 10 anos e fornece os parâmetros de custo. |
        """)

    df = _load()
    fc_map = _fc_medios()

    if df.empty:
        st.warning("Tabela raw_pde_parametro vazia. Execute `pi ingest` primeiro.")
        return

    # ── Sidebar sliders ───────────────────────────────────────────────────────
    with st.sidebar:
        st.divider()
        st.subheader("Sensibilidade econômica")
        wacc_pct = st.slider("WACC (%)", 4.0, 15.0, 8.0, step=0.5)
        capex_mult = st.slider("Multiplicador CAPEX", 0.7, 1.3, 1.0, step=0.05)
        wacc = wacc_pct / 100.0

    df = df.copy()
    df["capex_adj"] = df["capex_rs_kw"].fillna(0) * capex_mult
    df["crf_calc"] = df["vida_anos"].apply(lambda n: _crf(wacc, n) if pd.notna(n) else 0.0)
    df["custo_anual_rs_kw_ano"] = df["capex_adj"] * df["crf_calc"] + df["om_fixo_rs_kw_ano"].fillna(0)
    df["tech_label"] = df["tecnologia"].map(TECH_LABEL).fillna(df["tecnologia"])

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    cols = st.columns(len(df))
    for i, row in df.iterrows():
        with cols[i]:
            color = TECH_COLOR.get(row["tecnologia"], "#aaa")
            st.markdown(
                f"""<div style='background:color-mix(in srgb, {color} 12%, #1a1d27);
                border:1px solid {color}44; border-radius:8px; padding:12px;
                text-align:center;'>
                <div style='color:{color};font-weight:700;font-size:0.85rem;
                text-transform:uppercase;'>{row['tech_label']}</div>
                <div style='font-size:1.3rem;font-weight:700;margin:4px 0;'>
                {row['capex_adj']:,.0f}</div>
                <div style='color:#7a82a8;font-size:0.75rem;'>R$/kW CAPEX</div>
                <div style='margin-top:6px;font-size:0.9rem;'>
                CRF {row['crf_calc']:.3f}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("")

    # ── Grouped bar CAPEX / OM / CVU ─────────────────────────────────────────
    st.subheader("Componentes de custo por tecnologia")
    st.caption("Comparação dos três tipos de custo. Note que CAPEX e OM estão em R$/kW (custo por unidade de capacidade), enquanto CVU está em R$/MWh (custo por unidade de energia gerada) — as escalas são incomparáveis entre si; use para comparar tecnologias dentro de cada componente.")

    df_melt = df.melt(
        id_vars=["tecnologia", "tech_label"],
        value_vars=["capex_adj", "om_fixo_rs_kw_ano", "cvu_rs_mwh"],
        var_name="componente",
        value_name="valor",
    )
    comp_label = {
        "capex_adj": "CAPEX (R$/kW)",
        "om_fixo_rs_kw_ano": "OM fixo (R$/kW/ano)",
        "cvu_rs_mwh": "CVU (R$/MWh)",
    }
    df_melt["componente"] = df_melt["componente"].map(comp_label)

    fig_bar = px.bar(
        df_melt,
        x="tech_label", y="valor",
        color="componente",
        barmode="group",
        color_discrete_sequence=["#4f8ef7", "#4ff7a2", "#f7744f"],
        labels={"tech_label": "Tecnologia", "valor": "Valor", "componente": "Componente"},
    )
    fig_bar.update_layout(height=340, margin=dict(t=10, b=0))
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── Curva CRF × WACC ─────────────────────────────────────────────────────
    st.subheader("Sensibilidade do CRF ao WACC por tecnologia")
    st.caption("O CRF sobe com o WACC e cai com a vida útil mais longa. Tecnologias de longa maturação (hidro, 30+ anos) são mais sensíveis ao WACC: uma variação de 1 ponto percentual no WACC impacta muito mais o custo anualizado de um projeto de 30 anos do que de um de 15.")

    wacc_range = np.linspace(0.04, 0.15, 80)
    fig_crf = go.Figure()
    for _, row in df.iterrows():
        if pd.isna(row["vida_anos"]) or row["vida_anos"] <= 0:
            continue
        crfs = [_crf(w, row["vida_anos"]) for w in wacc_range]
        color = TECH_COLOR.get(row["tecnologia"], "#aaa")
        fig_crf.add_trace(go.Scatter(
            x=wacc_range * 100, y=crfs,
            mode="lines",
            name=f"{row['tech_label']} ({int(row['vida_anos'])}a)",
            line=dict(color=color, width=2),
        ))

    fig_crf.add_vline(x=wacc_pct, line_dash="dot", line_color="white",
                      annotation_text=f"WACC={wacc_pct:.1f}%", annotation_position="top right")
    fig_crf.update_layout(
        height=320,
        xaxis_title="WACC (%)", yaxis_title="CRF",
        legend=dict(orientation="h", y=1.08),
        margin=dict(t=10, b=0),
    )
    st.plotly_chart(fig_crf, use_container_width=True)

    # ── Waterfall LCOE ────────────────────────────────────────────────────────
    st.divider()
    st.subheader("LCOE estimado por tecnologia — decomposição dos componentes")
    st.caption(
        "LCOE (Custo Nivelado de Energia) em R$/MWh = (CAPEX × CRF + OM fixo) ÷ (FC médio × 8.760 h/ano) + CVU. "
        "Quanto maior o FC médio, mais horas de geração \"diluem\" o custo fixo de capital. "
        "FC médio vem da série histórica do ONS quando disponível; caso contrário usa referência conservadora."
    )

    WACC_VAL = wacc
    lcoe_rows = []
    for _, row in df.iterrows():
        tech = row["tecnologia"]
        # tenta FC médio ponderado do stg; fallback por tech
        fc_default = {"sol": 0.22, "eol": 0.38, "hidro": 0.55, "term": 0.85}
        fc_vals = [v for (s, t), v in fc_map.items() if t == tech and v > 0]
        fc_med = float(np.mean(fc_vals)) if fc_vals else fc_default.get(tech, 0.3)

        capex = row["capex_adj"]
        om = row["om_fixo_rs_kw_ano"] or 0
        cvu = row["cvu_rs_mwh"] or 0
        crf_v = row["crf_calc"]

        horas_eq = fc_med * 8760  # horas equivalentes por ano
        lcoe_capex = (capex * crf_v * 1000) / horas_eq if horas_eq > 0 else 0
        lcoe_om = (om * 1000) / horas_eq if horas_eq > 0 else 0
        lcoe_total = lcoe_capex + lcoe_om + cvu

        lcoe_rows.append({
            "tech_label": TECH_LABEL.get(tech, tech),
            "tecnologia": tech,
            "CAPEX×CRF": round(lcoe_capex, 1),
            "OM fixo": round(lcoe_om, 1),
            "CVU": round(cvu, 1),
            "LCOE total": round(lcoe_total, 1),
            "FC médio": round(fc_med, 3),
        })

    df_lcoe = pd.DataFrame(lcoe_rows)

    fig_wf = go.Figure()
    componentes = ["CAPEX×CRF", "OM fixo", "CVU"]
    c_colors = ["#4f8ef7", "#4ff7a2", "#f7744f"]
    for comp, color in zip(componentes, c_colors):
        fig_wf.add_trace(go.Bar(
            x=df_lcoe["tech_label"],
            y=df_lcoe[comp],
            name=comp,
            marker_color=color,
        ))

    fig_wf.update_layout(
        barmode="stack",
        height=340,
        xaxis_title="", yaxis_title="R$/MWh",
        margin=dict(t=10, b=0),
        legend=dict(orientation="h", y=1.08),
    )
    st.plotly_chart(fig_wf, use_container_width=True)
    st.dataframe(df_lcoe[["tech_label", "FC médio", "CAPEX×CRF", "OM fixo", "CVU", "LCOE total"]]
                 .rename(columns={"tech_label": "Tecnologia"}),
                 use_container_width=True, hide_index=True)

    # ── Heatmap sensibilidade LCOE × WACC × CAPEX ─────────────────────────────
    st.divider()
    st.subheader("Análise de sensibilidade do LCOE — WACC × multiplicador de CAPEX")
    st.caption(
        "Cada célula mostra o LCOE (R$/MWh) para uma combinação de WACC e fator multiplicador do CAPEX base. "
        "Multiplicador 1,0x = custo-base do PDE; 0,7x = queda de 30% no custo de capital (ex.: avanço tecnológico); 1,3x = custo 30% maior. "
        "Cores verdes = mais barato; vermelhas = mais caro. Útil para avaliar robustez da decisão de expansão."
    )

    tech_exp = [r for r in df.to_dict("records") if r.get("is_expansivel")]
    if not tech_exp:
        st.info("Nenhuma tecnologia expansível nos parâmetros.")
        return

    wacc_grid = np.linspace(0.04, 0.15, 25)
    capex_grid = np.linspace(0.7, 1.3, 25)

    heat_cols = st.columns(len(tech_exp))
    for idx, row in enumerate(tech_exp):
        tech = row["tecnologia"]
        fc_vals = [v for (s, t), v in fc_map.items() if t == tech and v > 0]
        fc_med = float(np.mean(fc_vals)) if fc_vals else {"sol": 0.22, "eol": 0.38}.get(tech, 0.25)
        n = row["vida_anos"] or 20
        base_capex = row["capex_rs_kw"] or 0
        om = row["om_fixo_rs_kw_ano"] or 0
        cvu = row["cvu_rs_mwh"] or 0

        horas_eq = fc_med * 8760
        mat = np.zeros((len(capex_grid), len(wacc_grid)))
        for i, cm in enumerate(capex_grid):
            for j, w in enumerate(wacc_grid):
                crf_v = _crf(w, n)
                capex_adj = base_capex * cm
                lcoe = (capex_adj * crf_v * 1000 + om * 1000) / horas_eq + cvu
                mat[i, j] = round(lcoe, 1)

        df_heat = pd.DataFrame(
            mat,
            index=[f"{c:.2f}x" for c in capex_grid],
            columns=[f"{w*100:.1f}%" for w in wacc_grid],
        )
        fig_h = px.imshow(
            df_heat,
            color_continuous_scale="RdYlGn_r",
            aspect="auto",
            labels={"x": "WACC", "y": "Mult. CAPEX", "color": "LCOE R$/MWh"},
            title=f"{TECH_LABEL.get(tech, tech)} — LCOE (R$/MWh)",
        )
        fig_h.update_layout(height=320, margin=dict(t=40, b=0))
        heat_cols[idx].plotly_chart(fig_h, use_container_width=True)
