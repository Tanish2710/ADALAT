import pytest

import database as db


@pytest.fixture
def circle(admin, user):
    carol = db.create_user("Carol", "carol@example.com", owner_id=admin["user_id"])
    gid = db.create_group("Flat 4B", owner_id=admin["user_id"])
    for uid in (admin["user_id"], user["user_id"], carol):
        db.add_member_to_group(gid, uid)
    return gid, admin["user_id"], user["user_id"], carol


@pytest.mark.parametrize("total,weights", [(100, [1, 1, 1]), (10, [1] * 7), (999.99, [3, 2, 5]), (0.05, [1, 1])])
def test_allocation_adds_up_to_the_cent(total, weights):
    parts = db.allocate_amounts(total, weights)
    assert round(sum(parts), 2) == round(total, 2)
    for part, w in zip(parts, weights):  # each part is within a cent of its exact share
        assert abs(part - total * w / sum(weights)) < 0.01


def test_allocation_rejects_zero_weights():
    with pytest.raises(ValueError):
        db.allocate_amounts(10, [0, 0])


def test_equal_split_and_payer_share_is_paid(circle):
    gid, a, b, c = circle
    sid = db.add_shared_expense(gid, a, 100, "Groceries")
    splits = {s["user_id"]: s for s in db.get_splits_for_expense(sid)}
    assert round(sum(s["amount_owed"] for s in splits.values()), 2) == 100
    assert splits[a]["is_paid"] == 1 and splits[b]["is_paid"] == 0


def test_custom_splits_must_match_total(circle):
    gid, a, b, c = circle
    with pytest.raises(ValueError):
        db.add_shared_expense(gid, a, 100, "Bad", custom_splits={a: 50, b: 40})
    db.add_shared_expense(gid, a, 100, "Good", custom_splits={a: 50, b: 30, c: 20})


def test_circle_names_are_unique_per_owner(admin, user):
    db.create_group("Trip", owner_id=admin["user_id"])
    with pytest.raises(ValueError):
        db.create_group("Trip", owner_id=admin["user_id"])
    db.create_group("Trip", owner_id=user["user_id"])  # another owner may reuse the name


def test_users_only_see_their_circles(circle, user):
    gid = circle[0]
    other = db.create_group("Not yours", owner_id=circle[1])
    visible = {g["group_id"] for g in db.get_visible_groups(user)}
    assert gid in visible and other not in visible
