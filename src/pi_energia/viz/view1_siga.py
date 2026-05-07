"""View 1 — Parque Gerador (SIGA + SIGET)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pi_energia.config import UF_TO_SUB
from pi_energia.viz.queries import linhas_geo, ref_mva, siga_usinas, siget_interligacao, siget_linhas_raw

TECH_COLOR = {
    "UFV": "#f7d24f",
    "EOL": "#4fcff7",
    "UHE": "#4f8ef7",
    "PCH": "#4f8ef7",
    "CGH": "#4f8ef7",
    "UTE": "#f7744f",
    "UTN": "#f7744f",
}
KV_LINE_COLOR = {
    800: "#ff4444",
    600: "#ff8800",
    500: "#ffcc00",
    345: "#aaffaa",
    230: "#aaddff",
    138: "#8888ff",
}
SUB_ORDER = ["N", "NE", "S", "SE_CO"]


def _agregar_interligacao(linhas_raw: pd.DataFrame, mva_ref_df: pd.DataFrame) -> pd.DataFrame:
    """Agrega linhas individuais em MVA por (sub_origem, sub_destino, kV), igual ao stg_siget."""
    mva_ref = {int(r["kV"]): (r["mva_ref"], r["fator_potencia"]) for _, r in mva_ref_df.iterrows()}
    df = linhas_raw.copy()
    df["sub_o"] = df["uf_orig"].map(UF_TO_SUB)
    df["sub_d"] = df["uf_dest"].map(UF_TO_SUB)
    df = df.dropna(subset=["sub_o", "sub_d", "kV"])
    inter = df[df["sub_o"] != df["sub_d"]].copy()
    inter["kV_int"] = inter["kV"].round().astype(int)
    # canoniza par com ordem lexicográfica para simetria
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
    usinas = siga_usinas()
    usinas["dat_entrada"] = pd.to_datetime(usinas["dat_entrada"], errors="coerce")
    usinas["ano_entrada"] = usinas["dat_entrada"].dt.year
    linhas_raw_siget = siget_interligacao()
    mva_ref_df = ref_mva()
    interlig = _agregar_interligacao(linhas_raw_siget, mva_ref_df)
    linhas = siget_linhas_raw()
    linhas_mapa = linhas_geo()
    return usinas, interlig, linhas, linhas_mapa


def render():
    st.header("View 1 — Parque Gerador (SIGA + SIGET)")
    st.caption(
        "Cadastro completo das usinas do Sistema Interligado Nacional (SIN) "
        "e da rede de transmissão de alta tensão."
    )

    with st.expander("📖 Glossário desta view", expanded=False):
        st.markdown("""
| Termo | Significado |
|-------|-------------|
| **SIGA** | Sistema de Informações de Geração da ANEEL — cadastro oficial de todas as usinas registradas no Brasil (operando, em construção ou planejadas). |
| **SIGET** | Sistema de Informações de Gestão da Transmissão — cadastro das linhas de transmissão e subestações do ONS. |
| **SIN** | Sistema Interligado Nacional — a rede elétrica que conecta quase todo o Brasil. |
| **UFV** | Usina Fotovoltaica (solar). |
| **EOL** | Usina Eólica. |
| **UHE** | Usina Hidrelétrica de grande porte. |
| **PCH / CGH** | Pequena Central Hidrelétrica / Central Geradora Hidrelétrica (hidros de menor porte). |
| **UTE** | Usina Termelétrica (gás, carvão, óleo, biomassa, etc.). |
| **UTN** | Usina Termonuclear. |
| **MW (Megawatt)** | Unidade de potência instalada. É o tamanho nominal da usina — quanto ela consegue gerar no máximo. |
| **Fase** | Ciclo de vida da usina: *Operação* = já gera; *Construção* = obras em andamento; *Planejamento* = aprovada mas não iniciada. |
| **Subsistema** | Divisão elétrico-geográfica do SIN: **N** (Norte), **NE** (Nordeste), **S** (Sul), **SE_CO** (Sudeste/Centro-Oeste). Cada subsistema tem geração e demanda próprias, conectados por linhas inter-regionais. |
| **kV (kilovolt)** | Tensão da linha de transmissão. Tensões maiores (500 kV, 800 kV) permitem transportar mais potência a longas distâncias com menos perdas. |
| **MVA (megavolt-ampere)** | Capacidade de potência aparente de uma linha ou transformador. Análogo ao MW, mas inclui componente reativa. No modelo, é usado como proxy da capacidade de intercâmbio entre subsistemas. |
| **Circuito** | Cada terna de cabos condutores numa linha de transmissão. Uma mesma torre pode carregar 1 ou 2 circuitos (dupla-terna). |
        """)

    usinas, interlig, linhas, linhas_mapa = _load()

    # ── Filtros ──────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        fases = st.multiselect(
            "Fase da usina",
            usinas["fase"].dropna().unique().tolist(),
            default=["Operação"],
            help="Ciclo de vida: Operação = já gera energia; Construção = obras em andamento; Planejamento = aprovada mas não iniciada.",
        )
    with col2:
        tipos = st.multiselect(
            "Tipo de geração (SIGA)",
            sorted(usinas["tipo_siga"].dropna().unique().tolist()),
            default=sorted(usinas["tipo_siga"].dropna().unique().tolist()),
            help="Siglas ANEEL: UFV=Solar, EOL=Eólica, UHE=Hidrelétrica grande, PCH/CGH=Hidro pequena, UTE=Termelétrica, UTN=Nuclear.",
        )
    with col3:
        mw_min = st.slider(
            "Potência mínima (MW)",
            0.0, 500.0, 0.0, step=10.0,
            help="Filtra usinas com potência outorgada ou fiscalizada abaixo deste valor. MW = megawatt, unidade de capacidade instalada.",
        )
    with col4:
        mostrar_linhas = st.checkbox(
            "Mostrar linhas de transmissão",
            value=True,
            help="Sobrepõe as linhas de alta tensão do SIGET/ONS sobre o mapa de usinas.",
        )
        kv_min_linha = st.selectbox(
            "Tensão mínima das linhas (kV)",
            [138, 230, 345, 500, 600, 800],
            index=2,
            help="Kilovolt (kV): tensão elétrica da linha. Linhas de maior tensão transportam mais potência a longas distâncias. 345 kV já filtra a backbone inter-regional.",
        )

    df = usinas.copy()
    if fases:
        df = df[df["fase"].isin(fases)]
    if tipos:
        df = df[df["tipo_siga"].isin(tipos)]
    df = df[df["mw"].fillna(0) >= mw_min]
    df_geo = df.dropna(subset=["lat", "lon"])

    st.caption(f"{len(df):,} usinas · {df['mw'].sum():,.0f} MW total filtrado")

    # ── Mapa ─────────────────────────────────────────────────────────────────
    if not df_geo.empty:
        fig_map = px.scatter_map(
            df_geo,
            lat="lat", lon="lon",
            color="tipo_siga",
            size="mw",
            size_max=18,
            hover_name="NomEmpreendimento",
            hover_data={"CodCEG": True, "uf": True, "mw": ":.1f", "fase": True, "lat": False, "lon": False},
            color_discrete_map=TECH_COLOR,
            zoom=3,
            center={"lat": -15, "lon": -52},
            map_style="carto-darkmatter",
            title="Usinas do SIGA",
        )

        if mostrar_linhas:
            df_lt = linhas_mapa[linhas_mapa["kv"] >= kv_min_linha].copy()
            kv_levels = sorted(df_lt["kv"].dropna().unique(), reverse=True)
            for kv in kv_levels:
                sub = df_lt[df_lt["kv"] == kv]
                color = KV_LINE_COLOR.get(int(kv), "#888888")
                # cada linha é um segmento: orig → dest → None (para quebrar traços)
                lats, lons, texts = [], [], []
                for _, r in sub.iterrows():
                    lats += [r["lat_orig"], r["lat_dest"], None]
                    lons += [r["lon_orig"], r["lon_dest"], None]
                    texts += [r["nome"], r["nome"], None]
                fig_map.add_trace(go.Scattermap(
                    lat=lats, lon=lons,
                    mode="lines",
                    line=dict(color=color, width=1),
                    name=f"{int(kv)} kV",
                    hovertext=texts,
                    hoverinfo="text",
                    legendgroup="lt",
                    legendgrouptitle_text="Transmissão" if kv == kv_levels[0] else None,
                ))

        fig_map.update_layout(height=560, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Nenhuma usina com coordenadas para os filtros selecionados.")

    # ── Sunburst + Histograma + Timeline ─────────────────────────────────────
    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.subheader("Composição da capacidade instalada por subsistema")
        st.caption("Cada fatia mostra a potência total (MW) de cada tecnologia dentro do subsistema. O anel externo é o tipo de geração; o interno é o subsistema.")
        agg = (
            df.dropna(subset=["subsistema"])
            .groupby(["subsistema", "tipo_siga"], as_index=False)["mw"]
            .sum()
        )
        fig_sun = px.sunburst(
            agg,
            path=["subsistema", "tipo_siga"],
            values="mw",
            color="tipo_siga",
            color_discrete_map=TECH_COLOR,
        )
        fig_sun.update_layout(height=380, margin=dict(t=10, b=0))
        st.plotly_chart(fig_sun, use_container_width=True)

    with col_b:
        st.subheader("Distribuição de portes das usinas (MW)")
        st.caption("Histograma em escala logarítmica no eixo X: a maioria das usinas é pequena (< 10 MW), mas poucos grandes projetos respondem pela maior parte da capacidade total.")
        fig_hist = px.histogram(
            df[df["mw"] > 0],
            x="mw",
            color="tipo_siga",
            log_x=True,
            nbins=60,
            color_discrete_map=TECH_COLOR,
            labels={"mw": "MW (escala log)", "tipo_siga": "Tipo"},
        )
        fig_hist.update_layout(height=380, bargap=0.05, margin=dict(t=10, b=0))
        st.plotly_chart(fig_hist, use_container_width=True)

    # ── Timeline entrada em operação ─────────────────────────────────────────
    st.subheader("Histórico de entrada em operação")
    st.caption("MW de capacidade adicionado a cada ano por tipo de geração. Permite ver ondas de expansão (ex.: boom eólico no NE na década de 2010, aceleração solar após 2018).")
    df_tl = (
        df.dropna(subset=["ano_entrada"])
        .groupby(["ano_entrada", "tipo_siga"], as_index=False)["mw"]
        .sum()
    )
    df_tl = df_tl[df_tl["ano_entrada"].between(1950, 2030)]
    fig_tl = px.bar(
        df_tl,
        x="ano_entrada", y="mw",
        color="tipo_siga",
        color_discrete_map=TECH_COLOR,
        labels={"ano_entrada": "Ano", "mw": "MW adicionado", "tipo_siga": "Tipo"},
    )
    fig_tl.update_layout(height=280, margin=dict(t=10, b=0))
    st.plotly_chart(fig_tl, use_container_width=True)

    # ── Transmissão — barras empilhadas por par × kV ─────────────────────────
    st.divider()
    st.subheader("Capacidade de interligação entre subsistemas (SIGET)")
    st.caption(
        "MVA total de linhas ativas entre cada par de subsistemas, por nível de tensão. "
        "Esta capacidade define o limite superior de intercâmbio de energia entre regiões."
    )

    interlig["par"] = interlig["sub_origem"] + " ↔ " + interlig["sub_destino"]
    fig_tx = px.bar(
        interlig.sort_values("kV"),
        x="par", y="mva_total",
        color="kV",
        color_continuous_scale="Plasma",
        text="n_circuitos",
        labels={"mva_total": "MVA total", "kV": "Tensão (kV)", "par": "Par inter-regional"},
        title="MVA por par de subsistemas e nível de tensão",
    )
    fig_tx.update_layout(height=340, margin=dict(t=40, b=0))
    st.plotly_chart(fig_tx, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("Comprimento × tensão por linha")
        st.caption("Cada ponto é uma linha de transmissão ativa. Linhas muito longas em alta tensão (500+ kV) são as que conectam regiões distantes.")
        linhas_ativas = linhas[linhas["DscSitLinTms"] == "Ativa"].copy()
        linhas_ativas["kv_cat"] = linhas_ativas["kv"].astype(str) + " kV"
        fig_sc = px.scatter(
            linhas_ativas.dropna(subset=["km", "kv"]),
            x="km", y="kv",
            color="kv_cat",
            size_max=8,
            opacity=0.6,
            hover_name="NomLinTms",
            hover_data={"uf_orig": True, "uf_dest": True, "kv_cat": False},
            labels={"km": "Comprimento (km)", "kv": "Tensão (kV)"},
        )
        fig_sc.update_layout(height=320, margin=dict(t=10, b=0))
        st.plotly_chart(fig_sc, use_container_width=True)

    with col_d:
        st.subheader("Distribuição de comprimentos por tensão")
        st.caption("Linhas de 138–230 kV tendem a ser curtas (distribuição local). Linhas de 500+ kV são as grandes autoestradas de energia — mais longas e menos numerosas.")
        fig_hkv = px.histogram(
            linhas_ativas.dropna(subset=["km", "kv"]),
            x="km", color="kv_cat",
            nbins=50,
            labels={"km": "Comprimento (km)", "kv_cat": "Tensão"},
        )
        fig_hkv.update_layout(height=320, margin=dict(t=10, b=0))
        st.plotly_chart(fig_hkv, use_container_width=True)
