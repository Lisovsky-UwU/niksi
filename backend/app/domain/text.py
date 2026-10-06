"""Russian money and date wording shared by chat messages (bot replies, notifications)."""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from html import escape

from app.domain.limits import limit_crossing

MONTHS_NOMINATIVE = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
MONTHS_GENITIVE = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]
MONTHS_PREPOSITIONAL = [
    "январе", "феврале", "марте", "апреле", "мае", "июне",
    "июле", "августе", "сентябре", "октябре", "ноябре", "декабре",
]
MONTHS_SHORT = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]

NBSP = " "


def money(value: Decimal | int | float) -> str:
    """1500.5 -> "1 500,5 ₽", 1500 -> "1 500 ₽" (non-breaking spaces, as in the web app)."""
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sign = "−" if amount < 0 else ""
    amount = abs(amount)
    whole, _, cents = f"{amount:.2f}".partition(".")
    groups = []
    while len(whole) > 3:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    groups.insert(0, whole)
    text = NBSP.join(groups)
    cents = cents.rstrip("0")
    if cents:
        text += "," + cents
    return f"{sign}{text}{NBSP}₽"


def signed_money(value: Decimal) -> str:
    return ("+" if value > 0 else "") + money(value)


def day_month(day: date) -> str:
    """date(2026, 9, 5) -> "5 сентября"."""
    return f"{day.day} {MONTHS_GENITIVE[day.month - 1]}"


def short_day(day: date) -> str:
    """date(2026, 9, 5) -> "5 сен"."""
    return f"{day.day} {MONTHS_SHORT[day.month - 1]}"


def plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


# ---- chat message building blocks (Telegram HTML) ----


def card(icon: str, title: str, *blocks: str | None) -> str:
    """A chat message with a clear shape: an icon and a bold title, then blocks of lines
    separated by empty lines. Empty blocks are skipped."""
    parts = [f"{icon} <b>{title}</b>"]
    parts.extend(block for block in blocks if block)
    return "\n\n".join(parts)


def quote(text: str) -> str:
    """A comment set apart from the numbers, so it reads as what the money went on."""
    return f"<blockquote>{escape(text)}</blockquote>"


def limit_warning(category_name: str, limit: Decimal, spent_before: Decimal, spent_after: Decimal) -> str | None:
    """A line for the chat when this expense pushed the category past 80% or past its limit."""
    crossed = limit_crossing(limit, spent_before, spent_after)
    name = escape(category_name)
    if crossed == "close":
        return f"⚠️ <b>Почти весь лимит:</b> в «{name}» потрачено больше 80%, осталось {money(limit - spent_after)}"
    if crossed == "over":
        return f"🔴 <b>Лимит превышен:</b> в «{name}» перерасход {money(spent_after - limit)}"
    return None


def expense_card(
    icon: str,
    title: str,
    amount: Decimal,
    category_name: str,
    spender_name: str | None,
    comment: str | None,
    limit: Decimal,
    spent_after: Decimal,
) -> str:
    """The same card for an expense recorded in the chat and one announced from the web app."""
    what = [f"💸 <b>{money(amount)}</b>, {escape(category_name)}"]
    if spender_name:
        what.append(f"👤 {escape(spender_name)}")
    if comment:
        what.append(quote(comment))
    status: list[str] = []
    if limit > 0:
        left = limit - spent_after
        status.append(
            f"📊 В категории осталось <b>{money(left)}</b> из {money(limit)}"
            if left >= 0
            else f"📊 В категории перерасход <b>{money(-left)}</b>, лимит {money(limit)}"
        )
    warning = limit_warning(category_name, limit, spent_after - amount, spent_after)
    if warning:
        status.append(warning)
    return card(icon, title, "\n".join(what), "\n".join(status))
