"""Shared fixtures: every test gets its own empty SQLite database and fast password hashing."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth  # noqa: E402
import database as db  # noqa: E402

PASSWORD = "correct1horse"


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    # Real hashes use 600k iterations; a few hundred keeps the suite fast and still exercises the format.
    monkeypatch.setattr(auth, "PBKDF2_ITERATIONS", 500)
    monkeypatch.delenv("REQUIRE_EMAIL_VERIFICATION", raising=False)
    auth._failures.clear()
    db.init_db()
    yield


@pytest.fixture
def admin():
    account, err = auth.sign_up("Asha Admin", "asha@example.com", PASSWORD, PASSWORD)
    assert err is None
    return account


@pytest.fixture
def user(admin):
    account, err = auth.sign_up("Ravi User", "ravi@example.com", PASSWORD, PASSWORD)
    assert err is None
    return account
