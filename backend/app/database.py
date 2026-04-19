from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import OUTPUTS_DIR


def database_url() -> str:
    default_path = OUTPUTS_DIR / "workbench.db"
    return os.getenv("SCNU_DATABASE_URL", f"sqlite:///{default_path}").strip()


class Base(DeclarativeBase):
    pass


engine = None
SessionLocal = sessionmaker(autoflush=False, autocommit=False, future=True)


def get_engine():
    global engine
    if engine is None:
        url = database_url()
        if url.startswith("sqlite"):
            sqlite_path = url.removeprefix("sqlite:///")
            if sqlite_path and sqlite_path != ":memory:":
                Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args, future=True)
        SessionLocal.configure(bind=engine)
    return engine


def init_db() -> None:
    # Import models before create_all so SQLAlchemy registers metadata.
    from . import models as _models  # noqa: F401

    active_engine = get_engine()
    Base.metadata.create_all(bind=active_engine)
    bootstrap_schema()


SCHEMA_BOOTSTRAP_COLUMNS = {
    "thesis_projects": {
        "school": {"sqlite": "VARCHAR(80) NOT NULL DEFAULT 'scnu'", "postgresql": "VARCHAR(80) NOT NULL DEFAULT 'scnu'"},
        "degree_level": {"sqlite": "VARCHAR(80) NOT NULL DEFAULT 'undergraduate'", "postgresql": "VARCHAR(80) NOT NULL DEFAULT 'undergraduate'"},
        "template_profile": {"sqlite": "VARCHAR(120) NOT NULL DEFAULT 'scnu-undergraduate'", "postgresql": "VARCHAR(120) NOT NULL DEFAULT 'scnu-undergraduate'"},
        "rule_set_id": {"sqlite": "VARCHAR(120) NOT NULL DEFAULT 'scnu-undergraduate-2025'", "postgresql": "VARCHAR(120) NOT NULL DEFAULT 'scnu-undergraduate-2025'"},
        "department": {"sqlite": "VARCHAR(200) NOT NULL DEFAULT ''", "postgresql": "VARCHAR(200) NOT NULL DEFAULT ''"},
        "major": {"sqlite": "VARCHAR(200) NOT NULL DEFAULT ''", "postgresql": "VARCHAR(200) NOT NULL DEFAULT ''"},
        "advisor": {"sqlite": "VARCHAR(120) NOT NULL DEFAULT ''", "postgresql": "VARCHAR(120) NOT NULL DEFAULT ''"},
        "student_name": {"sqlite": "VARCHAR(120) NOT NULL DEFAULT ''", "postgresql": "VARCHAR(120) NOT NULL DEFAULT ''"},
        "student_id": {"sqlite": "VARCHAR(120) NOT NULL DEFAULT ''", "postgresql": "VARCHAR(120) NOT NULL DEFAULT ''"},
        "writing_stage": {"sqlite": "VARCHAR(80) NOT NULL DEFAULT 'draft'", "postgresql": "VARCHAR(80) NOT NULL DEFAULT 'draft'"},
        "privacy_mode": {"sqlite": "VARCHAR(80) NOT NULL DEFAULT 'local_only'", "postgresql": "VARCHAR(80) NOT NULL DEFAULT 'local_only'"},
        "remote_provider_allowed": {"sqlite": "BOOLEAN NOT NULL DEFAULT 0", "postgresql": "BOOLEAN NOT NULL DEFAULT false"},
    },
    "provider_configs": {
        "verification_status": {"sqlite": "VARCHAR(40) NOT NULL DEFAULT 'untested'", "postgresql": "VARCHAR(40) NOT NULL DEFAULT 'untested'"},
        "verification_message": {"sqlite": "TEXT NOT NULL DEFAULT ''", "postgresql": "TEXT NOT NULL DEFAULT ''"},
        "last_verified_at": {"sqlite": "DATETIME", "postgresql": "TIMESTAMP"},
        "deleted_at": {"sqlite": "DATETIME", "postgresql": "TIMESTAMP"},
    },
    "exports": {
        "expires_at": {"sqlite": "DATETIME", "postgresql": "TIMESTAMP"},
        "deleted_at": {"sqlite": "DATETIME", "postgresql": "TIMESTAMP"},
    },
}


def bootstrap_schema() -> None:
    """Additive compatibility layer for local SQLite/Postgres installs before Alembic."""
    active_engine = get_engine()
    inspector = inspect(active_engine)
    existing_tables = set(inspector.get_table_names())
    dialect = active_engine.dialect.name
    with active_engine.begin() as connection:
        for table, columns in SCHEMA_BOOTSTRAP_COLUMNS.items():
            if table not in existing_tables:
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table)}
            for name, declarations in columns.items():
                if name in existing_columns:
                    continue
                declaration = declarations.get(dialect) or declarations["sqlite"]
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}"))


def get_db() -> Generator[Session, None, None]:
    init_db()
    with SessionLocal() as session:
        yield session
