from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.db.database import transaction


@dataclass(frozen=True)
class User:
    id: int
    email: str
    created_at: str


@dataclass(frozen=True)
class LoginCode:
    id: int
    email: str
    code_hash: str
    created_at: str
    expires_at: str
    used_at: str | None
    attempt_count: int


@dataclass(frozen=True)
class SessionRecord:
    id: int
    user_id: int
    token_hash: str
    created_at: str
    expires_at: str
    revoked_at: str | None


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_user(email: str, created_at: datetime, *, db_path: Path | None = None) -> User:
    normalized = normalize_email(email)
    if not normalized:
        raise ValueError("email must not be empty")

    with transaction(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO users (email, created_at) VALUES (?, ?)",
            (normalized, created_at.isoformat()),
        )
        return User(
            id=int(cursor.lastrowid),
            email=normalized,
            created_at=created_at.isoformat(),
        )


def find_user_by_email(email: str, *, db_path: Path | None = None) -> User | None:
    with transaction(db_path) as connection:
        row = connection.execute(
            "SELECT id, email, created_at FROM users WHERE email = ?",
            (normalize_email(email),),
        ).fetchone()

    return None if row is None else User(**dict(row))


def get_or_create_user(
    email: str,
    created_at: datetime,
    *,
    db_path: Path | None = None,
) -> User:
    existing = find_user_by_email(email, db_path=db_path)
    return existing or create_user(email, created_at, db_path=db_path)


def invalidate_active_login_codes(email: str, used_at: datetime, *, db_path: Path | None = None) -> None:
    with transaction(db_path) as connection:
        connection.execute(
            """
            UPDATE login_codes
            SET used_at = ?
            WHERE email = ? AND used_at IS NULL
            """,
            (used_at.isoformat(), normalize_email(email)),
        )


def create_login_code(
    email: str,
    code_hash: str,
    created_at: datetime,
    expires_at: datetime,
    *,
    db_path: Path | None = None,
) -> int:
    with transaction(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO login_codes (email, code_hash, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (normalize_email(email), code_hash, created_at.isoformat(), expires_at.isoformat()),
        )
        return int(cursor.lastrowid)


def find_latest_login_code(email: str, *, db_path: Path | None = None) -> LoginCode | None:
    with transaction(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, email, code_hash, created_at, expires_at, used_at, attempt_count
            FROM login_codes
            WHERE email = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (normalize_email(email),),
        ).fetchone()

    return None if row is None else LoginCode(**dict(row))


def increment_login_code_attempts(code_id: int, *, db_path: Path | None = None) -> None:
    with transaction(db_path) as connection:
        connection.execute(
            "UPDATE login_codes SET attempt_count = attempt_count + 1 WHERE id = ?",
            (code_id,),
        )


def mark_login_code_used(code_id: int, used_at: datetime, *, db_path: Path | None = None) -> None:
    with transaction(db_path) as connection:
        connection.execute(
            "UPDATE login_codes SET used_at = ? WHERE id = ? AND used_at IS NULL",
            (used_at.isoformat(), code_id),
        )


def create_session(
    user_id: int,
    token_hash: str,
    created_at: datetime,
    expires_at: datetime,
    *,
    db_path: Path | None = None,
) -> int:
    with transaction(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO sessions (user_id, token_hash, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, token_hash, created_at.isoformat(), expires_at.isoformat()),
        )
        return int(cursor.lastrowid)


def find_session_by_token_hash(token_hash: str, *, db_path: Path | None = None) -> SessionRecord | None:
    with transaction(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, user_id, token_hash, created_at, expires_at, revoked_at
            FROM sessions
            WHERE token_hash = ?
            """,
            (token_hash,),
        ).fetchone()

    return None if row is None else SessionRecord(**dict(row))


def find_user_by_id(user_id: int, *, db_path: Path | None = None) -> User | None:
    with transaction(db_path) as connection:
        row = connection.execute(
            "SELECT id, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    return None if row is None else User(**dict(row))


def revoke_session(session_id: int, revoked_at: datetime, *, db_path: Path | None = None) -> None:
    with transaction(db_path) as connection:
        connection.execute(
            "UPDATE sessions SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL",
            (revoked_at.isoformat(), session_id),
        )
