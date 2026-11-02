import auth


def test_hash_round_trip():
    stored = auth.hash_password("s3cret-pass")
    assert stored.startswith("pbkdf2_sha256$")
    assert auth.verify_password("s3cret-pass", stored)
    assert not auth.verify_password("wrong-pass1", stored)


def test_hashes_are_salted():
    assert auth.hash_password("same1pass") != auth.hash_password("same1pass")


def test_verify_rejects_malformed_hashes():
    for stored in (None, "", "plain", "md5$1$a$b", "pbkdf2_sha256$x$y$z"):
        assert not auth.verify_password("anything1", stored)


def test_hash_keeps_its_iteration_count(monkeypatch):
    """Hashes made with an older iteration count still verify after it changes."""
    monkeypatch.setattr(auth, "PBKDF2_ITERATIONS", 300)
    stored = auth.hash_password("legacy1pass")
    monkeypatch.setattr(auth, "PBKDF2_ITERATIONS", 900)
    assert auth.verify_password("legacy1pass", stored)


def test_password_rules():
    assert auth.password_problem("short1") is not None            # too short
    assert auth.password_problem("lettersonly") is not None       # no digit
    assert auth.password_problem("12345678") is not None          # no letter
    assert auth.password_problem("good1pass", "other1pass") is not None  # mismatch
    assert auth.password_problem("good1pass", "good1pass") is None
