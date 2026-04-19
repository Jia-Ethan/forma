from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .config import OUTPUTS_DIR


@dataclass(frozen=True)
class StoredObject:
    key: str
    sha256: str
    size: int


class ObjectStorage(Protocol):
    def put_bytes(self, key: str, payload: bytes) -> StoredObject: ...
    def get_bytes(self, key: str) -> bytes: ...
    def exists(self, key: str) -> bool: ...
    def delete(self, key: str) -> None: ...
    def delete_prefix(self, prefix: str) -> None: ...


class LocalObjectStorage:
    def __init__(self, root: Path | None = None):
        self.root = root or Path(os.getenv("SCNU_STORAGE_DIR", str(OUTPUTS_DIR / "storage")))
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe_key = key.strip().lstrip("/")
        target = (self.root / safe_key).resolve()
        target.relative_to(self.root.resolve())
        return target

    def put_bytes(self, key: str, payload: bytes) -> StoredObject:
        digest = hashlib.sha256(payload).hexdigest()
        target = self._path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        return StoredObject(key=key, sha256=digest, size=len(payload))

    def get_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists() and path.is_file():
            path.unlink()

    def delete_prefix(self, prefix: str) -> None:
        path = self._path(prefix)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


class S3CompatibleObjectStorage:
    """Reserved adapter boundary for COS/R2/S3 without coupling MVP to remote storage."""

    def __init__(self, endpoint_url: str, bucket: str):
        self.endpoint_url = endpoint_url
        self.bucket = bucket

    def put_bytes(self, key: str, payload: bytes) -> StoredObject:
        raise NotImplementedError("S3-compatible storage is reserved for a future backend.")

    def get_bytes(self, key: str) -> bytes:
        raise NotImplementedError("S3-compatible storage is reserved for a future backend.")

    def exists(self, key: str) -> bool:
        raise NotImplementedError("S3-compatible storage is reserved for a future backend.")

    def delete(self, key: str) -> None:
        raise NotImplementedError("S3-compatible storage is reserved for a future backend.")

    def delete_prefix(self, prefix: str) -> None:
        raise NotImplementedError("S3-compatible storage is reserved for a future backend.")


storage: ObjectStorage = LocalObjectStorage()
