"""Dashboard Streamlit — PI Energia."""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="PI Energia — Exploração de Dados",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# dark theme override via custom CSS
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #13151f; }
[data-testid="stAppViewContainer"] { background: #0f1117; }
.block-container { padding-top: 1.5rem; }
h1, h2, h3 { color: #dde2f5; }
</style>
""", unsafe_allow_html=True)

from pi_energia.viz import view1_siga, view2_demanda, view3_fc, view4_transmissao, view5_economia

VIEWS = {
    "1 · Parque Gerador (SIGA)": view1_siga.render,
    "2 · Demanda (ONS)": view2_demanda.render,
    "3 · Disponibilidade Renovável (FC)": view3_fc.render,
    "4 · Transmissão (SIGET)": view4_transmissao.render,
    "5 · Parâmetros Econômicos (PDE)": view5_economia.render,
}

with st.sidebar:
    st.title("⚡ PI Energia")
    st.caption("Exploração de dados — SIN brasileiro")
    st.divider()
    view_sel = st.radio("View", list(VIEWS.keys()))

VIEWS[view_sel]()
