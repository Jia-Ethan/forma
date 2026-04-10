from __future__ import annotations

from typing import Optional


class AppError(Exception):
    def __init__(self, code: str, message: str, *, details: Optional[dict] = None, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
