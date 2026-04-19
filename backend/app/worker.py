from __future__ import annotations

import time
from datetime import UTC, datetime
import json
import os
from pathlib import Path

from .config import OUTPUTS_DIR
from .database import init_db
from .database import SessionLocal
from .models import ExportRecord
from .storage import storage


def cleanup_expired_exports() -> int:
    now = datetime.now(UTC).replace(tzinfo=None)
    deleted = 0
    init_db()
    with SessionLocal() as db:
        rows = db.query(ExportRecord).filter(ExportRecord.expires_at.isnot(None), ExportRecord.expires_at < now, ExportRecord.deleted_at.is_(None)).all()
        for row in rows:
            if row.storage_key:
                storage.delete(row.storage_key)
            row.deleted_at = now
            row.status = "expired"
            deleted += 1
        db.commit()
    storage.delete_prefix("public/uploads")
    cleanup_public_exports()
    return deleted


def cleanup_public_exports() -> int:
    storage_root = Path(os.getenv("SCNU_STORAGE_DIR", str(OUTPUTS_DIR / "storage")))
    root = storage_root / "public" / "exports"
    if not root.exists():
        return 0
    now = datetime.now(UTC).replace(tzinfo=None)
    deleted = 0
    for meta_path in root.glob("*/meta.json"):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            expires_at = datetime.fromisoformat(meta["expires_at"])
        except Exception:
            continue
        if expires_at < now:
            storage.delete_prefix(f"public/exports/{meta_path.parent.name}")
            deleted += 1
    return deleted


def main() -> None:
    init_db()
    print("SCNU Workbench worker ready. Queue integration is reserved for Celery/Redis jobs.")
    while True:
        cleanup_expired_exports()
        time.sleep(60)


if __name__ == "__main__":
    main()
