from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from app.auth.repository import find_latest_login_code, find_user_by_email
from app.auth.service import (
    ExpiredCode,
    InvalidCode,
    TooManyAttempts,
    authenticate_session,
    logout,
    request_login_code,
    verify_login_code,
)
from app.db.database import initialize_database


class AuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "samogo-test.db"
        initialize_database(self.db_path)
        self.now = datetime(2026, 9, 21, 10, 0, tzinfo=UTC)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @patch("app.auth.service.secrets.randbelow", return_value=123456)
    def test_request_stores_hash_not_plain_code(self, _randbelow) -> None:
        challenge = request_login_code("Anna@Example.com", now=self.now, db_path=self.db_path)
        record = find_latest_login_code("anna@example.com", db_path=self.db_path)

        self.assertEqual(challenge.code, "123456")
        self.assertIsNotNone(record)
        self.assertNotEqual(record.code_hash, "123456")

    @patch("app.auth.service.secrets.randbelow", side_effect=[111111, 222222])
    def test_new_code_invalidates_previous_code(self, _randbelow) -> None:
        request_login_code("anna@example.com", now=self.now, db_path=self.db_path)
        request_login_code(
            "anna@example.com",
            now=self.now + timedelta(seconds=1),
            db_path=self.db_path,
        )

        with self.assertRaises(InvalidCode):
            verify_login_code("anna@example.com", "111111", now=self.now + timedelta(seconds=2), db_path=self.db_path)

    @patch("app.auth.service.secrets.randbelow", return_value=123456)
    def test_correct_code_creates_user_and_session(self, _randbelow) -> None:
        request_login_code("anna@example.com", now=self.now, db_path=self.db_path)
        session = verify_login_code(
            "anna@example.com",
            "123456",
            now=self.now + timedelta(seconds=1),
            db_path=self.db_path,
        )

        self.assertEqual(session.user.email, "anna@example.com")
        self.assertIsNotNone(find_user_by_email("anna@example.com", db_path=self.db_path))
        self.assertEqual(
            authenticate_session(session.token, now=self.now + timedelta(minutes=1), db_path=self.db_path),
            session.user,
        )

    @patch("app.auth.service.secrets.randbelow", return_value=123456)
    def test_code_is_one_time(self, _randbelow) -> None:
        request_login_code("anna@example.com", now=self.now, db_path=self.db_path)
        verify_login_code("anna@example.com", "123456", now=self.now, db_path=self.db_path)

        with self.assertRaises(InvalidCode):
            verify_login_code("anna@example.com", "123456", now=self.now, db_path=self.db_path)

    @patch("app.auth.service.secrets.randbelow", return_value=123456)
    def test_expired_code_is_rejected(self, _randbelow) -> None:
        request_login_code("anna@example.com", now=self.now, db_path=self.db_path)

        with self.assertRaises(ExpiredCode):
            verify_login_code(
                "anna@example.com",
                "123456",
                now=self.now + timedelta(minutes=11),
                db_path=self.db_path,
            )

    @patch("app.auth.service.secrets.randbelow", return_value=123456)
    def test_attempt_limit_blocks_code(self, _randbelow) -> None:
        request_login_code("anna@example.com", now=self.now, db_path=self.db_path)

        for _ in range(5):
            with self.assertRaises(InvalidCode):
                verify_login_code("anna@example.com", "000000", now=self.now, db_path=self.db_path)

        with self.assertRaises(TooManyAttempts):
            verify_login_code("anna@example.com", "123456", now=self.now, db_path=self.db_path)

    @patch("app.auth.service.secrets.randbelow", return_value=123456)
    def test_logout_revokes_session(self, _randbelow) -> None:
        request_login_code("anna@example.com", now=self.now, db_path=self.db_path)
        session = verify_login_code("anna@example.com", "123456", now=self.now, db_path=self.db_path)

        logout(session.token, now=self.now, db_path=self.db_path)

        self.assertIsNone(authenticate_session(session.token, now=self.now, db_path=self.db_path))


if __name__ == "__main__":
    unittest.main()
