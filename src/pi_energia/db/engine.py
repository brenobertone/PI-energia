"""SQLAlchemy engine (SQLite single-file).

This module ensures the local SQLite file exists. If the file is missing (e.g., in
a fresh deployment), it will attempt to download a release asset from GitHub
so the app can run without manual intervention.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from pi_energia.config import DB_PATH, DB_URL


RELEASE_TAG = "v1.0"
RELEASE_ASSET_URL = (
    f"https://github.com/brenobertone/PI-energia/releases/download/{RELEASE_TAG}/pi.db"
)


def _ensure_db_present() -> None:
    """Download the DB release asset if the sqlite file is missing.

    This is intentionally simple: it streams the remote file to disk and
    raises a RuntimeError on failure. The function is a no-op when the file
    already exists.
    """
    if DB_PATH.exists():
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        print(f"Downloading database from {RELEASE_ASSET_URL} to {DB_PATH} ...", flush=True)
        req = urllib.request.Request(RELEASE_ASSET_URL, headers={"User-Agent": "pi-energia/streamlit"})
        with urllib.request.urlopen(req) as resp, open(DB_PATH, "wb") as out:
            chunk_size = 1024 * 1024
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out.write(chunk)
        print("Database download completed.", flush=True)
    except Exception as exc:  # pragma: no cover - runtime network/io errors
        # Clean partial file if created
        try:
            if DB_PATH.exists():
                DB_PATH.unlink()
        except Exception:
            pass
        raise RuntimeError(f"Failed to download DB from {RELEASE_ASSET_URL}: {exc}") from exc


def get_engine(echo: bool = False) -> Engine:
    # Ensure DB is present before creating the engine. In local development
    # this is a fast no-op when the file already exists.
    _ensure_db_present()

    engine = create_engine(DB_URL, echo=echo, future=True)

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.close()

    return engine
