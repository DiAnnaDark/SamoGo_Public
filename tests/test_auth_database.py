from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.auth.repository import (
    create_login_code,
    create_session,
    create_user,
    find_user_by_email,
    increment_login_code_attempts,
    mark_login_code_used,
    revoke_session,
)
from app.db.database import connect, initialize_database


class AuthDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "samogo-test.db"
        initialize_database(self.db_path)
        self.now = datetime(2026, 9, 21, 9, 0, tzinfo=UTC)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_schema_contains_auth_tables(self) -> None:
        with connect(self.db_path) as connection:
            names = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }

        self.assertTrue({"users", "login_codes", "sessions"} <= names)

    def test_user_email_is_normalized_and_unique(self) -> None:
        user = create_user("  Anna@Example.COM ", self.now, db_path=self.db_path)

        self.assertEqual(user.email, "anna@example.com")
        self.assertEqual(
            find_user_by_email("ANNA@example.com", db_path=self.db_path),
            user,
        )

        with self.assertRaises(sqlite3.IntegrityError):
            create_user("anna@example.com", self.now, db_path=self.db_path)

    def test_login_code_tracks_expiry_usage_and_attempts(self) -> None:
        expires_at = self.now + timedelta(minutes=10)
        code_id = create_login_code(
            "anna@example.com",
            "hashed-code",
            self.now,
            expires_at,
            db_path=self.db_path,
        )

        increment_login_code_attempts(code_id, db_path=self.db_path)
        mark_login_code_used(code_id, self.now, db_path=self.db_path)

        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT code_hash, expires_at, used_at, attempt_count
                FROM login_codes
                WHERE id = ?
                """,
                (code_id,),
            ).fetchone()

        self.assertEqual(row["code_hash"], "hashed-code")
        self.assertEqual(row["expires_at"], expires_at.isoformat())
        self.assertEqual(row["used_at"], self.now.isoformat())
        self.assertEqual(row["attempt_count"], 1)

    def test_session_requires_existing_user_and_can_be_revoked(self) -> None:
        user = create_user("anna@example.com", self.now, db_path=self.db_path)
        expires_at = self.now + timedelta(days=30)

        session_id = create_session(
            user.id,
            "hashed-session-token",
            self.now,
            expires_at,
            db_path=self.db_path,
        )
        revoke_session(session_id, self.now, db_path=self.db_path)

        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT revoked_at FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()

        self.assertEqual(row["revoked_at"], self.now.isoformat())

        with self.assertRaises(sqlite3.IntegrityError):
            create_session(
                999999,
                "another-token",
                self.now,
                expires_at,
                db_path=self.db_path,
            )

    def test_deleting_user_cascades_sessions(self) -> None:
        user = create_user("anna@example.com", self.now, db_path=self.db_path)
        create_session(
            user.id,
            "hashed-session-token",
            self.now,
            self.now + timedelta(days=30),
            db_path=self.db_path,
        )

        with connect(self.db_path) as connection:
            connection.execute("DELETE FROM users WHERE id = ?", (user.id,))
            connection.commit()
            count = connection.execute(
                "SELECT COUNT(*) FROM sessions WHERE user_id = ?",
                (user.id,),
            ).fetchone()[0]

        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
