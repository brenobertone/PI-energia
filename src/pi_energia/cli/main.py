"""CLI principal: pi init-db | ingest | dashboard."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer

from pi_energia.db.init_schema import init_db
from pi_energia.etl import (
    raw_carga,
    raw_fc,
    raw_pde,
    raw_ref_mva,
    raw_siga,
    raw_siget,
    stg_dims,
    stg_siga,
    stg_subestacao,
)

app = typer.Typer(help="PI-energia — dashboard de exploração do SIN")


@app.command("init-db")
def cmd_init_db():
    """Cria o schema SQLite (idempotente)."""
    init_db()
    typer.echo("schema criado.")


@app.command("ingest")
def cmd_ingest(
    skip_fc: bool = typer.Option(
        False,
        "--skip-fc",
        help="pula o carregamento do fator de capacidade (lento)",
    ),
):
    """Ingere todos os datasets para a camada RAW e reconstrói as dims."""
    typer.echo("RAW...")
    typer.echo(f"  raw_pde: {raw_pde.ingest_raw_pde()}")
    typer.echo(f"  raw_ref_mva: {raw_ref_mva.ingest_raw_ref_mva()}")
    typer.echo(f"  raw_carga: {raw_carga.ingest_raw_carga()}")
    typer.echo(f"  raw_siga: {raw_siga.ingest_raw_siga()}")
    typer.echo(f"  raw_siget_linha: {raw_siget.ingest_raw_siget_linha()}")
    if not skip_fc:
        typer.echo("  raw_fc (lento)...")
        typer.echo(f"  raw_fc: {raw_fc.ingest_raw_fc()}")

    typer.echo("STAGING...")
    typer.echo(f"  dims: {stg_dims.build_dims()}")
    typer.echo(f"  stg_siga: {stg_siga.build_stg_siga()}")
    typer.echo(f"  stg_subestacao: {stg_subestacao.ingest_stg_subestacao()}")


@app.command("dashboard")
def cmd_dashboard(
    port: int = typer.Option(8501, help="porta do servidor Streamlit"),
):
    """Abre o dashboard de exploração de dados no navegador."""
    app_path = Path(__file__).resolve().parents[1] / "viz" / "app.py"
    creds = Path.home() / ".streamlit" / "credentials.toml"
    if not creds.exists():
        creds.parent.mkdir(parents=True, exist_ok=True)
        creds.write_text('[general]\nemail = ""\n')

    subprocess.run(
        [
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.port", str(port),
            "--browser.gatherUsageStats", "false",
        ],
        check=True,
    )


if __name__ == "__main__":
    app()
