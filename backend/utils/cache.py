from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import json
import uuid

from config.database import get_db, close_db, PipelineCache


def _now_utc() -> datetime:
    # Return timezone-naive datetime to match SQLite storage
    return datetime.utcnow()


def build_cache_key(namespace: str, identifier: str) -> str:
    """Create a stable cache key for a given namespace + identifier."""
    return f"{namespace}:{identifier}"


def get_cached_payload(namespace: str, identifier: str) -> Optional[Dict[str, Any]]:
    """Return cached JSON payload if present and not expired."""
    cache_key = build_cache_key(namespace, identifier)
    db = get_db()
    try:
        row = db.query(PipelineCache).filter(PipelineCache.cache_key == cache_key).first()
        if not row:
            return None
        if row.expires_at and row.expires_at < _now_utc():
            # Expired – delete lazily
            db.delete(row)
            db.commit()
            return None
        return row.payload or None
    finally:
        close_db(db)


def set_cached_payload(namespace: str, identifier: str, payload: Dict[str, Any], ttl_seconds: int = 900) -> None:
    """Store JSON-serializable payload with a simple TTL."""
    cache_key = build_cache_key(namespace, identifier)
    db = get_db()
    try:
        expires_at = _now_utc() + timedelta(seconds=ttl_seconds) if ttl_seconds > 0 else None
        row = db.query(PipelineCache).filter(PipelineCache.cache_key == cache_key).first()
        if row:
            row.payload = payload
            row.expires_at = expires_at
        else:
            row = PipelineCache(
                id=str(uuid.uuid4()),
                cache_key=cache_key,
                payload=payload,
                created_at=_now_utc(),
                expires_at=expires_at,
            )
            db.add(row)
        db.commit()
    finally:
        close_db(db)


