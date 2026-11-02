import auth
import database as db
from conftest import PASSWORD


def test_first_account_is_admin_and_later_ones_are_users(admin, user):
    assert admin["role"] == "admin"
    assert user["role"] == "user"


def test_first_account_adopts_existing_people_and_circles():
    contact = db.create_user("Old Contact", "old@example.com")
    gid = db.create_group("Old Circle")
    account, _ = auth.sign_up("First", "first@example.com", PASSWORD, PASSWORD)
    assert db.get_user(contact)["owner_id"] == account["user_id"]
    assert db.get_group(gid)["owner_id"] == account["user_id"]


def test_sign_up_validation(admin):
    assert auth.sign_up("", "x@example.com", PASSWORD, PASSWORD)[1]
    assert auth.sign_up("X", "not-an-email", PASSWORD, PASSWORD)[1]
    assert auth.sign_up("X", "x@example.com", "weak", "weak")[1]
    assert auth.sign_up("Dup", "ASHA@example.com", PASSWORD, PASSWORD)[1]  # emails are case-insensitive


def test_closed_sign_ups(admin):
    db.set_setting("signups_open", False)
    account, err = auth.sign_up("Late", "late@example.com", PASSWORD, PASSWORD)
    assert account is None and "turned off" in err


def test_contact_who_signs_up_takes_over_their_profile(admin):
    contact = db.create_user("Meera", "meera@example.com", owner_id=admin["user_id"])
    account, err = auth.sign_up("Meera", "meera@example.com", PASSWORD, PASSWORD)
    assert err is None
    assert account["user_id"] == contact
    assert account["owner_id"] is None


def test_login_and_logout(admin):
    account, err = auth.log_in("  Asha@Example.com ", PASSWORD)
    assert err is None and account["user_id"] == admin["user_id"]
    token = auth.start_session(admin["user_id"])
    assert auth.account_for_token(token)["user_id"] == admin["user_id"]
    auth.end_session(token)
    assert auth.account_for_token(token) is None
    assert auth.account_for_token(None) is None


def test_wrong_password_and_unknown_email_give_the_same_error(admin):
    _, wrong_pw = auth.log_in("asha@example.com", "nope1nope")
    _, unknown = auth.log_in("nobody@example.com", PASSWORD)
    assert wrong_pw == unknown


def test_lockout_after_repeated_failures(admin):
    for _ in range(auth.MAX_FAILURES):
        auth.log_in("asha@example.com", "wrong1pass")
    account, err = auth.log_in("asha@example.com", PASSWORD)
    assert account is None and "Too many attempts" in err


def test_deactivated_account_cannot_log_in(admin, user):
    db.set_account_active(user["user_id"], False)
    account, err = auth.log_in("ravi@example.com", PASSWORD)
    assert account is None and "deactivated" in err


def test_set_up_admin_creates_or_promotes(user):
    promoted, err = auth.set_up_admin("", "ravi@example.com", "new1password")
    assert err is None and promoted["role"] == "admin"
    assert auth.log_in("ravi@example.com", "new1password")[0] is not None
    created, err = auth.set_up_admin("Ops", "ops@example.com", "ops1password")
    assert err is None and created["role"] == "admin"


def test_email_verification_flow(monkeypatch, admin):
    monkeypatch.setenv("REQUIRE_EMAIL_VERIFICATION", "1")
    sent = {}
    monkeypatch.setattr(auth, "email_ready", lambda: True)
    monkeypatch.setattr(auth, "_send_code", lambda email, code, name="": sent.update(code=code) or (True, "sent"))
    email, err = auth.start_sign_up("Vik", "vik@example.com", PASSWORD, PASSWORD)
    assert err is None and db.get_account_by_email("vik@example.com") is None
    assert auth.verify_code(email, "000000" if sent["code"] != "000000" else "111111")[0] is None
    account, err = auth.verify_code(email, sent["code"])
    assert err is None and account["email"] == "vik@example.com"
