import logging
from typing import Dict, Any

from jose import JWTError, jwt
from fastapi import HTTPException

from config import JWT_SECRET, JWT_ALGORITHM

logger = logging.getLogger(__name__)


def _normalize_uuid(val: Any) -> str:
    """Normalize UUID values to lowercase string without braces."""
    if val is None:
        return ""
    return str(val).lower().strip("{}")


def validate_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token produced by the Django backend.
    Returns the decoded payload dict.
    Raises HTTPException 401 on any validation failure.
    """
    try:
        # Django Simple JWT uses HS256 by default
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_aud": False},  # Django JWT doesn't set 'aud'
        )
        # Django Simple JWT stores user_id in 'user_id' claim
        if "user_id" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        # Normalize UUID to lowercase for consistent DB comparison
        payload["user_id"] = _normalize_uuid(payload["user_id"])
        return payload
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

