"""
Security Utilities: Password Hashing, JWT Management, and Rate Limiting.
Direct bcrypt implementation (cost 12), PyJWT, and in-memory login throttling.
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple
import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import ThrottledException

# In-memory login rate limiter: (username, ip) -> list of timestamp floats
_FAILED_ATTEMPTS: Dict[Tuple[str, str], list] = {}
RATE_LIMIT_WINDOW_SECONDS = 15 * 60  # 15 minutes
MAX_FAILED_ATTEMPTS = 5


def hash_password(password: str) -> str:
    """Hash password using direct bcrypt with salt rounds 12."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    subject: str,
    role: str,
    student_id: Optional[str] = None,
    name: Optional[str] = None,
    department: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate signed JWT access token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,
        "role": role,
        "student_id": student_id,
        "name": name,
        "department": department,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    encoded = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded


def decode_access_token(token: str) -> Dict[str, any]:
    """Decode and validate signed JWT."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def record_failed_login(username: str, ip: str) -> None:
    """Record failed login timestamp for rate limiting."""
    now = time.time()
    key = (username.strip().lower(), ip.strip())
    history = _FAILED_ATTEMPTS.get(key, [])
    # Prune expired entries
    history = [t for t in history if now - t < RATE_LIMIT_WINDOW_SECONDS]
    history.append(now)
    _FAILED_ATTEMPTS[key] = history


def check_login_throttled(username: str, ip: str) -> None:
    """Raise ThrottledException (HTTP 429) if failed attempts exceed limit within window."""
    now = time.time()
    key = (username.strip().lower(), ip.strip())
    history = _FAILED_ATTEMPTS.get(key, [])
    valid_history = [t for t in history if now - t < RATE_LIMIT_WINDOW_SECONDS]
    _FAILED_ATTEMPTS[key] = valid_history

    if len(valid_history) >= MAX_FAILED_ATTEMPTS:
        raise ThrottledException("Too many failed login attempts. Please try again in 15 minutes.")


def reset_failed_login(username: str, ip: str) -> None:
    """Clear failed attempts upon successful login."""
    key = (username.strip().lower(), ip.strip())
    if key in _FAILED_ATTEMPTS:
        del _FAILED_ATTEMPTS[key]
