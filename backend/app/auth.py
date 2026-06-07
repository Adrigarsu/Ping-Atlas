import os

from fastapi import Header, HTTPException


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    raw = os.environ.get("API_KEYS", "")
    valid = {k.strip() for k in raw.split(",") if k.strip()}
    if not valid or x_api_key not in valid:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")