from app.services.rotation import pick_assignee


def test_simple_round_robin():
    order = [1, 2, 3]
    active = {1, 2, 3}
    assert pick_assignee(order, 0, active) == 1
    assert pick_assignee(order, 1, active) == 2
    assert pick_assignee(order, 2, active) == 3
    assert pick_assignee(order, 3, active) == 1
    assert pick_assignee(order, 7, active) == 2


def test_single_member_list():
    assert pick_assignee([42], 0, {42}) == 42
    assert pick_assignee([42], 5, {42}) == 42


def test_skips_inactive_member():
    # member 2 is gone -> next active in ring is 3
    assert pick_assignee([1, 2, 3], 1, {1, 3}) == 3


def test_wraps_when_skipping():
    # member 3 gone, occurrence_index=2 starts at 3 then wraps to 1
    assert pick_assignee([1, 2, 3], 2, {1, 2}) == 1


def test_all_inactive_returns_none():
    assert pick_assignee([1, 2], 0, set()) is None


def test_empty_rotation_returns_none():
    assert pick_assignee([], 0, {1, 2, 3}) is None
