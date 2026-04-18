from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import OUTPUTS_DIR


def database_url() -> str:
    default_path = OUTPUTS_DIR / "workbench.db"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    return os.getenv("SCNU_DATABASE_URL", f"sqlite:///{default_path}").strip()


class Base(DeclarativeBase):
    pass


DATABASE_URL = database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    # Import models before create_all so SQLAlchemy registers metadata.
    from . import models as _models  # noqa: F401

    Base.metadata.create_all(bind=engine)
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
}


def bootstrap_schema() -> None:
    """Additive compatibility layer for local SQLite/Postgres installs before Alembic."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    dialect = engine.dialect.name
    with engine.begin() as connection:
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
