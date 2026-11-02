import logic
import database as db
from test_circles import circle  # noqa: F401  (fixture)


def test_balances_net_to_zero(circle):
    gid, a, b, c = circle
    db.add_shared_expense(gid, a, 300, "Rent")
    db.add_shared_expense(gid, b, 90, "Dinner")
    bal = logic.compute_balances(gid)
    assert abs(sum(bal.values())) < 0.01
    assert bal == {a: 170.0, b: -40.0, c: -130.0}


def test_simplify_debts_uses_few_payments():
    balances = {1: 50.0, 2: 30.0, 3: -20.0, 4: -60.0}
    plan = logic.simplify_debts(balances)
    assert len(plan) <= len(balances) - 1
    after = dict(balances)
    for debtor, creditor, amount in plan:
        after[debtor] += amount
        after[creditor] -= amount
    assert all(abs(v) < 0.01 for v in after.values())


def test_simplify_debts_ignores_settled_people():
    assert logic.simplify_debts({1: 0.0, 2: 0.004, 3: -0.004}) == []


def test_paying_the_plan_settles_the_circle(circle):
    gid, a, b, c = circle
    db.add_shared_expense(gid, a, 300, "Rent")
    db.add_shared_expense(gid, b, 90, "Dinner")
    for debtor, creditor, amount in logic.simplify_debts(logic.compute_balances(gid)):
        db.add_settlement(debtor, creditor, amount, gid)
    assert all(abs(v) < 0.01 for v in logic.compute_balances(gid).values())
    assert logic.get_settlement_plan(gid) == []


def test_marking_a_share_paid_clears_it(circle):
    gid, a, b, c = circle
    sid = db.add_shared_expense(gid, a, 90, "Taxi")
    db.mark_user_paid_for_expense(sid, b)
    bal = logic.compute_balances(gid)
    assert bal[b] == 0 and bal[a] == 30.0 and bal[c] == -30.0


def test_all_circles_total_respects_scope(circle, admin):
    gid, a, b, c = circle
    other = db.create_group("Weekend", owner_id=a)
    db.add_member_to_group(other, a)
    db.add_member_to_group(other, b)
    db.add_shared_expense(gid, a, 30, "Snacks")
    db.add_shared_expense(other, b, 40, "Fuel")
    assert logic.compute_balances(group_ids=[gid])[b] == -10.0
    assert logic.compute_balances()[b] == 10.0


def test_sample_data_loads(admin):
    assert db.seed_comprehensive_demo_data(as_user_id=admin["user_id"])
    assert len(db.get_all_groups()) > 0
    assert abs(sum(logic.compute_balances().values())) < 0.01
