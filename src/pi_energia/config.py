"""Configuração global do pacote pi_energia.

Centraliza paths do repositório, mapeamentos UF→subsistema e constantes
usadas na formulação.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
DATASETS_DIR: Path = REPO_ROOT / "datasets"
DATA_DIR: Path = REPO_ROOT / "data"
DB_PATH: Path = DATA_DIR / "pi.db"
DB_URL: str = f"sqlite:///{DB_PATH}"

PDE_CUSTOS_YML: Path = DATA_DIR / "pde_custos.yml"
REF_MVA_YML: Path = DATA_DIR / "ref_mva_por_tensao.yml"

CARGA_PARQUET: Path = DATASETS_DIR / "carga_energia" / "CARGA_ENERGIA_2025.parquet"
FC_DIR: Path = DATASETS_DIR / "fator_capacidade_eolica_solar"
SIGA_CSV: Path = DATASETS_DIR / "siga" / "siga-empreendimentos-geracao.csv"
SIGET_LINHA_CSV: Path = (
    DATASETS_DIR
    / "SIGET - Contrato Módulo Linha Transmissão"
    / "siget-contrato-modulolinhatransmissao-subestacaoorigem-subestacaodestino.csv"
)
SUBESTACAO_PARQUET: Path = DATASETS_DIR / "subestacao_rede_operacoes" / "SUBESTACAO.parquet"

UF_TO_SUB: dict[str, str] = {}
for _uf in "MG ES RJ SP GO MT MS DF AC RO".split():
    UF_TO_SUB[_uf] = "SE_CO"
for _uf in "PR SC RS".split():
    UF_TO_SUB[_uf] = "S"
for _uf in "BA SE AL PE PB RN CE PI MA".split():
    UF_TO_SUB[_uf] = "NE"
for _uf in "PA AP AM RR TO".split():
    UF_TO_SUB[_uf] = "N"

SUBSISTEMAS: list[tuple[str, str]] = [
    ("N", "Norte"),
    ("NE", "Nordeste"),
    ("S", "Sul"),
    ("SE_CO", "Sudeste/Centro-Oeste"),
]

TECNOLOGIAS_DEFAULT: list[dict] = [
    {"sigla": "sol", "nome": "Solar FV", "familia": "renovavel"},
    {"sigla": "eol", "nome": "Eólica Onshore", "familia": "renovavel"},
    {"sigla": "hidro", "nome": "Hidro existente", "familia": "hidro"},
    {"sigla": "term", "nome": "Gás Natural 100% Flex", "familia": "termica"},
]

ONS_SUBSIS_LABEL_TO_SIGLA: dict[str, str] = {
    "Norte": "N",
    "Nordeste": "NE",
    "Sul": "S",
    "Sudeste/Centro-Oeste": "SE_CO",
}

ONS_TIPOUSINA_TO_TECH: dict[str, str] = {
    "Eólica": "eol",
    "Solar": "sol",
}

SIGA_TIPO_TO_TECH: dict[str, str] = {
    "UFV": "sol",
    "EOL": "eol",
    "UHE": "hidro",
    "PCH": "hidro",
    "CGH": "hidro",
    "UTE": "term",
    "UTN": "term",
}

HORAS_ANO: int = 8760
DIAS_MES: list[int] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
assert sum(DIAS_MES) * 24 == HORAS_ANO
