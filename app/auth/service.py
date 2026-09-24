from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.auth import repository


CODE_TTL = timedelta(minutes=10)
SESSION_TTL = timedelta(days=30)
MAX_CODE_ATTEMPTS = 5


class AuthError(Exception):
    pass


class InvalidCode(AuthError):
    pass


class ExpiredCode(AuthError):
    pass


class TooManyAttempts(AuthError):
    pass


@dataclass(frozen=True)
class LoginChallenge:
    email: str
    code: str
    expires_at: datetime


@dataclass(frozen=True)
class AuthenticatedSession:
    token: str
    user: repository.User
    expires_at: datetime


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def request_login_code(
    email: str,
    *,
    now: datetime | None = None,
    db_path: Path | None = None,
) -> LoginChallenge:
    current = now or utc_now()
    normalized = repository.normalize_email(email)
    if "@" not in normalized:
        raise ValueError("invalid email")

    repository.invalidate_active_login_codes(normalized, current, db_path=db_path)

    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = current + CODE_TTL
    repository.create_login_code(
        normalized,
        hash_secret(code),
        current,
        expires_at,
        db_path=db_path,
    )
    return LoginChallenge(email=normalized, code=code, expires_at=expires_at)


def verify_login_code(
    email: str,
    code: str,
    *,
    now: datetime | None = None,
    db_path: Path | None = None,
) -> AuthenticatedSession:
    current = now or utc_now()
    normalized = repository.normalize_email(email)
    record = repository.find_latest_login_code(normalized, db_path=db_path)

    if record is None or record.used_at is not None:
        raise InvalidCode("invalid login code")

    if record.attempt_count >= MAX_CODE_ATTEMPTS:
        raise TooManyAttempts("too many attempts")

    expires_at = datetime.fromisoformat(record.expires_at)
    if current >= expires_at:
        repository.mark_login_code_used(record.id, current, db_path=db_path)
        raise ExpiredCode("login code expired")

    if not hmac.compare_digest(record.code_hash, hash_secret(code)):
        repository.increment_login_code_attempts(record.id, db_path=db_path)
        raise InvalidCode("invalid login code")

    repository.mark_login_code_used(record.id, current, db_path=db_path)
    user = repository.get_or_create_user(normalized, current, db_path=db_path)

    token = secrets.token_urlsafe(32)
    session_expires_at = current + SESSION_TTL
    repository.create_session(
        user.id,
        hash_secret(token),
        current,
        session_expires_at,
        db_path=db_path,
    )
    return AuthenticatedSession(token=token, user=user, expires_at=session_expires_at)


def authenticate_session(
    token: str | None,
    *,
    now: datetime | None = None,
    db_path: Path | None = None,
) -> repository.User | None:
    if not token:
        return None

    current = now or utc_now()
    record = repository.find_session_by_token_hash(hash_secret(token), db_path=db_path)
    if record is None or record.revoked_at is not None:
        return None
    if current >= datetime.fromisoformat(record.expires_at):
        return None

    return repository.find_user_by_id(record.user_id, db_path=db_path)


def logout(
    token: str | None,
    *,
    now: datetime | None = None,
    db_path: Path | None = None,
) -> None:
    if not token:
        return

    record = repository.find_session_by_token_hash(hash_secret(token), db_path=db_path)
    if record is not None and record.revoked_at is None:
        repository.revoke_session(record.id, now or utc_now(), db_path=db_path)
