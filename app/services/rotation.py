"""Pure round-robin assignee selection. No DB access."""
from __future__ import annotations


def pick_assignee(
    rotation_order: list[int],
    occurrence_index: int,
    active_member_ids: set[int],
) -> int | None:
    """Pick the assignee for the Nth occurrence of a round-robin chore.

    Walks forward through the rotation starting at index N % len, skipping
    members that are no longer active. Returns None only if the rotation
    list is empty or every listed member is inactive.
    """
    if not rotation_order:
        return None
    n = len(rotation_order)
    start = occurrence_index % n
    for i in range(n):
        candidate = rotation_order[(start + i) % n]
        if candidate in active_member_ids:
            return candidate
    return None
