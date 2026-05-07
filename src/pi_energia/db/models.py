"""Schema SQLAlchemy: camadas RAW, STAGING e DIMENSIONAL."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# RAW
# ---------------------------------------------------------------------------
class RawCargaEnergia(Base):
    __tablename__ = "raw_carga_energia"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_subsistema: Mapped[str] = mapped_column(String(8), index=True)
    nom_subsistema: Mapped[str] = mapped_column(String(64))
    din_instante: Mapped[datetime] = mapped_column(DateTime, index=True)
    val_cargaenergiamwmed: Mapped[float] = mapped_column(Float)
    source_file: Mapped[str] = mapped_column(String(256))
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("id_subsistema", "din_instante", name="uq_raw_carga"),
    )


class RawFatorCapacidade(Base):
    __tablename__ = "raw_fator_capacidade"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_subsistema: Mapped[str] = mapped_column(String(8), index=True)
    nom_subsistema: Mapped[str] = mapped_column(String(64))
    id_estado: Mapped[str | None] = mapped_column(String(8), nullable=True)
    nom_estado: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cod_pontoconexao: Mapped[str | None] = mapped_column(String(32), nullable=True)
    nom_tipousina: Mapped[str] = mapped_column(String(16), index=True)
    nom_usina_conjunto: Mapped[str] = mapped_column(String(128), index=True)
    ceg: Mapped[str | None] = mapped_column(String(32), nullable=True)
    din_instante: Mapped[datetime] = mapped_column(DateTime, index=True)
    val_capacidadeinstalada: Mapped[float | None] = mapped_column(Float, nullable=True)
    val_geracaoverificada: Mapped[float | None] = mapped_column(Float, nullable=True)
    val_fatorcapacidade: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_file: Mapped[str] = mapped_column(String(256))
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint(
            "nom_usina_conjunto",
            "cod_pontoconexao",
            "din_instante",
            name="uq_raw_fc",
        ),
    )


class RawSigaUsina(Base):
    __tablename__ = "raw_siga_usina"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    CodCEG: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    NomEmpreendimento: Mapped[str | None] = mapped_column(String(256))
    SigUFPrincipal: Mapped[str | None] = mapped_column(String(4), index=True)
    SigTipoGeracao: Mapped[str | None] = mapped_column(String(8), index=True)
    DscFaseUsina: Mapped[str | None] = mapped_column(String(64), index=True)
    DscOrigemCombustivel: Mapped[str | None] = mapped_column(String(64))
    DscFonteCombustivel: Mapped[str | None] = mapped_column(String(128))
    NomFonteCombustivel: Mapped[str | None] = mapped_column(String(128))
    DatEntradaOperacao: Mapped[str | None] = mapped_column(String(32))
    MdaPotenciaOutorgadaKw: Mapped[float | None] = mapped_column(Float)
    MdaPotenciaFiscalizadaKw: Mapped[float | None] = mapped_column(Float)
    MdaGarantiaFisicaKw: Mapped[float | None] = mapped_column(Float)
    NumCoordNEmpreendimento: Mapped[float | None] = mapped_column(Float)
    NumCoordEEmpreendimento: Mapped[float | None] = mapped_column(Float)
    DscSubBacia: Mapped[str | None] = mapped_column(String(128))
    DscMuninicpios: Mapped[str | None] = mapped_column(String(256))
    source_file: Mapped[str] = mapped_column(String(256))
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class RawSigetLinha(Base):
    __tablename__ = "raw_siget_linha"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    IdeMdl: Mapped[int | None] = mapped_column(Integer)
    IdeLinTms: Mapped[int | None] = mapped_column(Integer, index=True)
    DscSitLinTms: Mapped[str | None] = mapped_column(String(32), index=True)
    NomLinTms: Mapped[str | None] = mapped_column(String(256))
    NumCcuLinTms: Mapped[str | None] = mapped_column(String(8))
    NumEtnLinTms_km: Mapped[float | None] = mapped_column(Float)
    NumTensaoBaseLinhaTransm_kV: Mapped[float | None] = mapped_column(Float, index=True)
    IdcTipoCircuitoLinhaTransm: Mapped[int | None] = mapped_column(Integer)
    IdeOnsSbeOrigem: Mapped[str | None] = mapped_column(String(32), index=True)
    NomSubestacaoOrigem: Mapped[str | None] = mapped_column(String(128))
    SigUFSubestacaoOrigem: Mapped[str | None] = mapped_column(String(4), index=True)
    IdeOnsSbeDestino: Mapped[str | None] = mapped_column(String(32), index=True)
    NomSubestacaoDestino: Mapped[str | None] = mapped_column(String(128))
    SigUFSubestacaoDestino: Mapped[str | None] = mapped_column(String(4), index=True)
    source_file: Mapped[str] = mapped_column(String(256))
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class StgSubestacao(Base):
    __tablename__ = "stg_subestacao"
    id_subestacao: Mapped[str] = mapped_column(String(32), primary_key=True)
    nom_subestacao: Mapped[str | None] = mapped_column(String(128))
    id_subsistema: Mapped[str | None] = mapped_column(String(8))
    id_estado: Mapped[str | None] = mapped_column(String(8))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)


class RawPdeParametro(Base):
    __tablename__ = "raw_pde_parametro"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tecnologia: Mapped[str] = mapped_column(String(16), index=True)
    variante: Mapped[str] = mapped_column(String(32), default="ref")
    nome: Mapped[str | None] = mapped_column(String(128))
    capex_rs_kw: Mapped[float | None] = mapped_column(Float)
    om_fixo_rs_kw_ano: Mapped[float | None] = mapped_column(Float)
    cvu_rs_mwh: Mapped[float | None] = mapped_column(Float)
    vida_anos: Mapped[float | None] = mapped_column(Float)
    bloco_mw: Mapped[float | None] = mapped_column(Float)
    is_expansivel: Mapped[bool] = mapped_column(Boolean, default=False)
    source_ref: Mapped[str] = mapped_column(String(256))
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("tecnologia", "variante", name="uq_raw_pde"),
    )


class RawRefMvaPorTensao(Base):
    __tablename__ = "raw_ref_mva_por_tensao"
    kV: Mapped[int] = mapped_column(Integer, primary_key=True)
    mva_ref: Mapped[float] = mapped_column(Float)
    fator_potencia: Mapped[float] = mapped_column(Float, default=0.95)
    fonte: Mapped[str] = mapped_column(String(256))
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ---------------------------------------------------------------------------
# DIMENSÕES
# ---------------------------------------------------------------------------
class DimSubsistema(Base):
    __tablename__ = "dim_subsistema"
    id_subsistema: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sigla: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(64))


class DimSnapshotAno(Base):
    __tablename__ = "dim_snapshot_ano"
    id_ano: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ano: Mapped[int] = mapped_column(Integer, unique=True)
    descricao: Mapped[str | None] = mapped_column(String(128))


class DimUsinaSiga(Base):
    __tablename__ = "dim_usina_siga"
    id_usina: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    CodCEG: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    id_subsistema: Mapped[int] = mapped_column(ForeignKey("dim_subsistema.id_subsistema"))
    uf: Mapped[str | None] = mapped_column(String(4))
    fase: Mapped[str | None] = mapped_column(String(64), index=True)
    mw_outorgada: Mapped[float | None] = mapped_column(Float)
    mw_fiscalizada: Mapped[float | None] = mapped_column(Float)
    mw_garantia_fisica: Mapped[float | None] = mapped_column(Float)
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)



