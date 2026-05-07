"""Queries SQL reutilizáveis para o dashboard Streamlit."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from pi_energia.db.session import SessionLocal


def _df(sql: str, **params) -> pd.DataFrame:
    with SessionLocal() as s:
        return pd.read_sql(text(sql), s.bind, params=params)


# ── View 1 — SIGA ────────────────────────────────────────────────────────────

def siga_usinas() -> pd.DataFrame:
    return _df("""
        SELECT
            u.CodCEG,
            u.NomEmpreendimento,
            u.SigUFPrincipal            AS uf,
            u.SigTipoGeracao            AS tipo_siga,
            u.DscFaseUsina              AS fase,
            u.DscFonteCombustivel       AS combustivel,
            u.DatEntradaOperacao        AS dat_entrada,
            COALESCE(
                u.MdaPotenciaFiscalizadaKw,
                u.MdaPotenciaOutorgadaKw
            ) / 1000.0                  AS mw,
            u.MdaGarantiaFisicaKw / 1000.0 AS mw_garantia,
            u.NumCoordNEmpreendimento   AS lat,
            u.NumCoordEEmpreendimento   AS lon,
            u.DscSubBacia               AS sub_bacia,
            d.sigla                     AS subsistema
        FROM raw_siga_usina u
        LEFT JOIN dim_usina_siga du ON du.CodCEG = u.CodCEG
        LEFT JOIN dim_subsistema d  ON d.id_subsistema = du.id_subsistema
        WHERE u.MdaPotenciaOutorgadaKw > 0
          OR  u.MdaPotenciaFiscalizadaKw > 0
    """)


def siget_interligacao() -> pd.DataFrame:
    return _df("""
        SELECT
            NomLinTms                    AS nome,
            NumTensaoBaseLinhaTransm_kV  AS kV,
            NumEtnLinTms_km              AS km,
            IdcTipoCircuitoLinhaTransm   AS n_circuitos,
            SigUFSubestacaoOrigem        AS uf_orig,
            SigUFSubestacaoDestino       AS uf_dest,
            NomSubestacaoOrigem          AS sube_orig,
            NomSubestacaoDestino         AS sube_dest,
            DscSitLinTms                 AS situacao
        FROM raw_siget_linha
        WHERE DscSitLinTms = 'Ativa'
          AND NumTensaoBaseLinhaTransm_kV IS NOT NULL
        ORDER BY NumTensaoBaseLinhaTransm_kV DESC
    """)


def siget_linhas_raw() -> pd.DataFrame:
    return _df("""
        SELECT
            IdeLinTms, DscSitLinTms, NomLinTms,
            NumEtnLinTms_km   AS km,
            NumTensaoBaseLinhaTransm_kV AS kv,
            IdcTipoCircuitoLinhaTransm  AS n_circuitos,
            IdeOnsSbeOrigem, NomSubestacaoOrigem, SigUFSubestacaoOrigem  AS uf_orig,
            IdeOnsSbeDestino, NomSubestacaoDestino, SigUFSubestacaoDestino AS uf_dest
        FROM raw_siget_linha
        WHERE NumTensaoBaseLinhaTransm_kV IS NOT NULL
    """)


# ── View 2 — Demanda ──────────────────────────────────────────────────────────

def carga_horaria() -> pd.DataFrame:
    return _df("""
        SELECT
            din_instante,
            CASE nom_subsistema
                WHEN 'Norte'                THEN 'N'
                WHEN 'Nordeste'             THEN 'NE'
                WHEN 'Sul'                  THEN 'S'
                WHEN 'Sudeste/Centro-Oeste' THEN 'SE_CO'
            END AS subsistema,
            val_cargaenergiamwmed AS mwmed
        FROM raw_carga_energia
        WHERE nom_subsistema IN ('Norte','Nordeste','Sul','Sudeste/Centro-Oeste')
        ORDER BY din_instante, nom_subsistema
    """)


# ── View 3 — FC Renováveis ────────────────────────────────────────────────────

def fc_horario_raw() -> pd.DataFrame:
    """FC horário por usina individual da camada RAW."""
    return _df("""
        SELECT
            din_instante,
            nom_usina_conjunto,
            CASE nom_subsistema
                WHEN 'Norte'                THEN 'N'
                WHEN 'Nordeste'             THEN 'NE'
                WHEN 'Sul'                  THEN 'S'
                WHEN 'Sudeste/Centro-Oeste' THEN 'SE_CO'
            END AS subsistema,
            CASE nom_tipousina
                WHEN 'Solar'  THEN 'sol'
                WHEN 'Eólica' THEN 'eol'
            END AS tecnologia,
            val_capacidadeinstalada AS mw_instalado,
            val_fatorcapacidade     AS fc
        FROM raw_fator_capacidade
        WHERE val_fatorcapacidade IS NOT NULL
          AND val_capacidadeinstalada IS NOT NULL
          AND nom_tipousina IN ('Solar', 'Eólica')
        ORDER BY din_instante, nom_usina_conjunto
    """)


def fc_por_usina() -> pd.DataFrame:
    """FC médio anual por usina (nom_usina_conjunto) da camada RAW."""
    return _df("""
        SELECT
            nom_usina_conjunto,
            id_subsistema,
            nom_tipousina        AS tipo_ons,
            COUNT(*)             AS n_horas,
            AVG(val_fatorcapacidade) AS fc_medio,
            MAX(val_capacidadeinstalada) AS mw_instalado
        FROM raw_fator_capacidade
        WHERE val_fatorcapacidade IS NOT NULL
          AND val_capacidadeinstalada IS NOT NULL
        GROUP BY nom_usina_conjunto, id_subsistema, nom_tipousina
        ORDER BY fc_medio DESC
    """)


def linhas_geo() -> pd.DataFrame:
    """Linhas de transmissão ativas com coordenadas de origem e destino."""
    return _df("""
        SELECT
            l.NomLinTms          AS nome,
            l.NumTensaoBaseLinhaTransm_kV AS kv,
            l.NumEtnLinTms_km    AS km,
            l.DscSitLinTms       AS situacao,
            so.nom_subestacao    AS nom_orig,
            so.lat               AS lat_orig,
            so.lon               AS lon_orig,
            sd.nom_subestacao    AS nom_dest,
            sd.lat               AS lat_dest,
            sd.lon               AS lon_dest
        FROM raw_siget_linha l
        JOIN stg_subestacao so
          ON UPPER(TRIM(l.IdeOnsSbeOrigem)) = so.id_subestacao
        JOIN stg_subestacao sd
          ON UPPER(TRIM(l.IdeOnsSbeDestino)) = sd.id_subestacao
        WHERE l.DscSitLinTms = 'Ativa'
          AND so.lat IS NOT NULL AND so.lon IS NOT NULL
          AND sd.lat IS NOT NULL AND sd.lon IS NOT NULL
        ORDER BY l.NumTensaoBaseLinhaTransm_kV DESC
    """)


# ── View 4 — Transmissão ──────────────────────────────────────────────────────

def ref_mva() -> pd.DataFrame:
    return _df("SELECT kV, mva_ref, fator_potencia FROM raw_ref_mva_por_tensao ORDER BY kV")


# ── View 5 — Economia ─────────────────────────────────────────────────────────

def pde_parametros() -> pd.DataFrame:
    return _df("""
        SELECT tecnologia, variante, capex_rs_kw, om_fixo_rs_kw_ano,
               cvu_rs_mwh, vida_anos, bloco_mw, is_expansivel
        FROM raw_pde_parametro
        ORDER BY tecnologia
    """)
