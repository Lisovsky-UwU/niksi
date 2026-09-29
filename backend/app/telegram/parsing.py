"""Understanding chat messages: an expense, an income receipt, or just conversation.

An expense is a free-form line in any order: "2000 подукты", "1500 дом и быт за
электричество", "кафе 300", or split over lines "кафе\\n500\\nакадемия кофе". The amount
is the first number; the category is found by its full name, by the start of one of its
words ("прод") or despite a typo ("подукты"); whatever is left is the comment.
"""

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

# 450 | 1 200 | 1200,50 | 450р | 450 руб. | 450₽ — digit groups may be split by spaces.
_AMOUNT = re.compile(
    r"(?<![\w+.,:])(?P<int>\d{1,3}(?:[  ]\d{3})+|\d+)(?:[.,](?P<frac>\d{1,2}))?(?![\d:])"
    r"(?:\s*(?:₽|р\b\.?|руб\b\.?|рубл\w*))?",
    re.IGNORECASE,
)
_WORD = re.compile(r"[^\W_]+(?:[-'][^\W_]+)*", re.UNICODE)

# An unrecognised message with more words than this is taken for conversation, not an expense.
MAX_WORDS_WITHOUT_CATEGORY = 4
_FUZZY_RATIO = 0.8
# "приду в 19", "до 5", "после 8": a number after these words is a time, not money.
_TIME_PREPOSITIONS = {"в", "во", "к", "ко", "до", "после", "с", "со", "около", "через", "на", "по", "от"}


def _looks_like_money(text: str, match: re.Match[str], categories: list[tuple[int, str]]) -> bool:
    """In everyday chat numbers are everywhere ("буду дома в 19 если не задержат"). An
    amount counts only at the start or the end of the message, alone on its own line, or
    right next to a category name ("здоровье 1200 аптека"), and never right after a word
    that makes it a time ("в 19")."""
    before, after = text[: match.start()], text[match.end() :]
    words_before = _WORD.findall(before)
    if words_before and _norm(words_before[-1]) in _TIME_PREPOSITIONS:
        return False
    at_start = not before.strip()
    at_end = not _WORD.search(after)
    own_line = any(line.strip() == match.group().strip() for line in text.splitlines())
    if at_start or at_end or own_line:
        return True
    words_after = _WORD.findall(after)
    neighbours = [w for w in (words_before[-1:] + words_after[:1])]
    tokens = [_Token(w, _norm(w), 0) for w in neighbours]
    matched, _ = _category_match(tokens, categories)
    return bool(matched)


def _norm(text: str) -> str:
    return text.casefold().replace("ё", "е")


def _amount(match: re.Match[str]) -> Decimal | None:
    whole = re.sub(r"\s", "", match.group("int"))
    try:
        value = Decimal(f"{whole}.{match.group('frac') or '0'}")
    except InvalidOperation:
        return None
    return value if value > 0 else None


@dataclass
class ParsedExpense:
    amount: Decimal
    comment: str | None
    category_id: int | None = None
    # Several equally good categories, or all of them when nothing matched: ask with buttons.
    candidates: list[int] = field(default_factory=list)


@dataclass
class _Token:
    text: str
    norm: str
    start: int


def _category_match(tokens: list[_Token], categories: list[tuple[int, str]]) -> tuple[list[int], set[int]]:
    """Best-matching category ids and the indexes of the tokens that named them."""
    # score: 3 full name, 2 start of a word, 1 typo; earlier position wins among equals.
    best: tuple[int, int] | None = None
    winners: dict[int, set[int]] = {}

    def offer(category_id: int, score: int, position: int, used: set[int]) -> None:
        nonlocal best
        key = (score, -position)
        if best is None or key > best:
            best = key
            winners.clear()
        if key == best:
            winners.setdefault(category_id, used)

    for category_id, name in categories:
        name_words = [_norm(w) for w in _WORD.findall(name)]
        if not name_words:
            continue
        # a) the whole name as a phrase, e.g. "дом и быт"
        n = len(name_words)
        for i in range(len(tokens) - n + 1):
            if [t.norm for t in tokens[i : i + n]] == name_words:
                offer(category_id, 3, i, set(range(i, i + n)))
        significant = [w for w in name_words if len(w) >= 3]
        for i, token in enumerate(tokens):
            if len(token.norm) < 3:
                continue
            # b) the start of a word of the name ("прод" -> "продукты")
            if any(w.startswith(token.norm) for w in significant):
                offer(category_id, 2, i, {i})
            # c) a typo ("подукты" -> "продукты")
            elif len(token.norm) >= 4 and any(
                SequenceMatcher(None, token.norm, w).ratio() >= _FUZZY_RATIO for w in significant
            ):
                offer(category_id, 1, i, {i})

    if not winners:
        return [], set()
    used = set().union(*winners.values())
    return list(winners), used


def parse_expense(text: str, categories: list[tuple[int, str]], forced: bool = False) -> ParsedExpense | None:
    """None when the message is not an expense (no amount, or chat with a stray number).

    With `forced` (the /add command) any message with an amount counts as an expense.
    """
    original_match = _AMOUNT.search(text)
    if original_match is None or (not forced and not _looks_like_money(text, original_match, categories)):
        return None
    flat = " ".join(text.split())
    amount_match = _AMOUNT.search(flat)
    if amount_match is None:
        return None
    amount = _amount(amount_match)
    if amount is None:
        return None

    rest = flat[: amount_match.start()] + " " + flat[amount_match.end() :]
    tokens = [_Token(m.group(), _norm(m.group()), m.start()) for m in _WORD.finditer(rest)]
    matched, used = _category_match(tokens, categories)

    comment_words = [t.text for i, t in enumerate(tokens) if i not in used]
    comment = " ".join(comment_words) or None

    if len(matched) == 1:
        return ParsedExpense(amount=amount, comment=comment, category_id=matched[0])
    if not matched and not forced and len(tokens) > MAX_WORDS_WITHOUT_CATEGORY:
        return None
    candidates = matched or [category_id for category_id, _ in categories]
    return ParsedExpense(amount=amount, comment=comment, candidates=candidates)


def parse_income(text: str) -> tuple[Decimal, str | None] | None:
    """"+40000 аванс" -> (40000, "аванс"). Only messages starting with a plus are income."""
    flat = " ".join(text.split())
    if not flat.startswith("+"):
        return None
    match = _AMOUNT.search(flat[1:].lstrip())
    if match is None or match.start() != 0:
        return None
    amount = _amount(match)
    if amount is None:
        return None
    body = flat[1:].lstrip()
    comment = (body[: match.start()] + body[match.end() :]).strip() or None
    return amount, comment


def parse_amount(text: str) -> Decimal | None:
    """The first amount in a command argument, e.g. "/grey 3000"."""
    match = _AMOUNT.search(" ".join(text.split()))
    return _amount(match) if match else None
