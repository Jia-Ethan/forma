from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time

from .config import access_code, secret_key


def access_token_for_current_code() -> str:
    code = access_code()
    if not code:
        return ""
    return hmac.new(secret_key().encode("utf-8"), f"access:{code}".encode("utf-8"), hashlib.sha256).hexdigest()


def verify_access_token(token: str | None) -> bool:
    expected = access_token_for_current_code()
    return bool(expected and token and hmac.compare_digest(token, expected))


def verify_access_code(candidate: str) -> bool:
    expected = access_code()
    return bool(expected and hmac.compare_digest(candidate.strip(), expected))


def thesis_digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def export_token_for_digest(digest: str, expires_at: int) -> str:
    body = f"export:{digest}:{expires_at}"
    signature = hmac.new(secret_key().encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"v1:{expires_at}:{digest}:{signature}"


def verify_export_token(token: str | None, digest: str) -> bool:
    if not token:
        return False
    parts = token.split(":")
    if len(parts) != 4 or parts[0] != "v1":
        return False
    try:
        expires_at = int(parts[1])
    except ValueError:
        return False
    if expires_at < int(time.time()) or parts[2] != digest:
        return False
    expected = export_token_for_digest(digest, expires_at)
    return hmac.compare_digest(token, expected)


def seal_secret(value: str) -> str:
    if not value:
        return ""
    nonce = os.urandom(16)
    payload = value.encode("utf-8")
    key = _secret_key_bytes()
    stream = _keystream(key, nonce, len(payload))
    cipher = bytes(left ^ right for left, right in zip(payload, stream, strict=True))
    mac = hmac.new(key, nonce + cipher, hashlib.sha256).digest()
    return "v1:" + base64.urlsafe_b64encode(nonce + mac + cipher).decode("ascii")


def open_secret(sealed: str) -> str:
    if not sealed:
        return ""
    if not sealed.startswith("v1:"):
        return ""
    raw = base64.urlsafe_b64decode(sealed[3:].encode("ascii"))
    nonce = raw[:16]
    mac = raw[16:48]
    cipher = raw[48:]
    key = _secret_key_bytes()
    expected = hmac.new(key, nonce + cipher, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected):
        return ""
    stream = _keystream(key, nonce, len(cipher))
    payload = bytes(left ^ right for left, right in zip(cipher, stream, strict=True))
    return payload.decode("utf-8")


def _secret_key_bytes() -> bytes:
    return hashlib.sha256(secret_key().encode("utf-8")).digest()


def _keystream(key: bytes, nonce: bytes, size: int) -> bytes:
    blocks: list[bytes] = []
    counter = 0
    while sum(len(block) for block in blocks) < size:
        blocks.append(hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest())
        counter += 1
    return b"".join(blocks)[:size]
