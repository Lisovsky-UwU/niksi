"""When a category's spending crosses a warning line.

The same thresholds as the web list (CategoryRow.vue): from 80% of the limit a category is
"close", above 100% it is "over". Only the moment of crossing is reported, so the chat gets
one warning per line, not one per expense.
"""

from decimal import Decimal
from typing import Literal

LimitState = Literal["ok", "close", "over"]

CLOSE_SHARE = Decimal("0.8")


def limit_state(limit: Decimal, spent: Decimal) -> LimitState:
    if limit <= 0:
        return "ok"
    if spent > limit:
        return "over"
    if spent >= limit * CLOSE_SHARE:
        return "close"
    return "ok"


def limit_crossing(limit: Decimal, spent_before: Decimal, spent_after: Decimal) -> LimitState | None:
    """The new state if spending moved it to a worse one, otherwise None."""
    order = {"ok": 0, "close": 1, "over": 2}
    before, after = limit_state(limit, spent_before), limit_state(limit, spent_after)
    return after if order[after] > order[before] else None
