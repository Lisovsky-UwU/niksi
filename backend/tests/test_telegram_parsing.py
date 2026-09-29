from decimal import Decimal

import pytest

from app.telegram.parsing import parse_amount, parse_expense, parse_income

CATEGORIES = [
    (1, "Продукты"),
    (2, "Кафе и доставка"),
    (3, "Транспорт"),
    (4, "Дом и быт"),
    (5, "Развлечения"),
    (6, "Здоровье"),
    (7, "Подарки"),
]


@pytest.mark.parametrize(
    ("text", "amount", "category", "comment"),
    [
        # The examples from the couple.
        ("2000 подукты", "2000", 1, None),
        ("1500 дом и быт за электричество", "1500", 4, "за электричество"),
        ("кафе 300", "300", 2, None),
        ("кафе\n500\nакадемия кофе", "500", 2, "академия кофе"),
        # Other everyday shapes.
        ("450 прод пятёрочка у дома", "450", 1, "пятёрочка у дома"),
        ("1 200 транспорт такси домой", "1200", 3, "такси домой"),
        ("трансп 350р", "350", 3, None),
        ("здоровье 1200,50 аптека", "1200.50", 6, "аптека"),
        ("Продукты 780 руб. вкусвилл", "780", 1, "вкусвилл"),
        ("подарок маме 2500", "2500", 7, "маме"),
    ],
)
def test_expenses_in_any_order(text: str, amount: str, category: int, comment: str | None) -> None:
    parsed = parse_expense(text, CATEGORIES)
    assert parsed is not None
    assert parsed.amount == Decimal(amount)
    assert parsed.category_id == category
    assert parsed.comment == comment


def test_no_amount_is_not_an_expense() -> None:
    assert parse_expense("купил продукты", CATEGORIES) is None
    assert parse_expense("", CATEGORIES) is None


def test_unknown_category_asks_with_all_categories() -> None:
    parsed = parse_expense("500 шаверма", CATEGORIES)
    assert parsed is not None
    assert parsed.category_id is None
    assert parsed.candidates == [c for c, _ in CATEGORIES]
    assert parsed.comment == "шаверма"


def test_chat_with_a_stray_number_is_ignored() -> None:
    assert parse_expense("буду дома в 19 если не задержат на работе", CATEGORIES) is None
    assert parse_expense("приду в 19", CATEGORIES) is None
    assert parse_expense("встретимся в кафе в 18:30", CATEGORIES) is None
    assert parse_expense("купили 2 кофе в кафе и пошли гулять", CATEGORIES) is None
    # ...unless it is sent with /add on purpose.
    forced = parse_expense("буду дома в 19 если не задержат на работе", CATEGORIES, forced=True)
    assert forced is not None and forced.amount == Decimal(19)


def test_equally_good_categories_are_offered_as_buttons() -> None:
    parsed = parse_expense("300 до", [(1, "Дом"), (2, "Доставка")], forced=True)
    # "до" is too short to name anything, so every category is offered.
    assert parsed is not None and parsed.category_id is None
    tie = parse_expense("300 дом", [(1, "Дом"), (2, "Домашние животные")])
    assert tie is not None
    # The full name beats the start of another word.
    assert tie.category_id == 1


def test_income_needs_a_leading_plus() -> None:
    assert parse_income("+40000 аванс") == (Decimal(40000), "аванс")
    assert parse_income("+ 45 000 зарплата") == (Decimal(45000), "зарплата")
    assert parse_income("+500") == (Decimal(500), None)
    assert parse_income("40000 аванс") is None
    assert parse_income("+аванс") is None


def test_amount_argument() -> None:
    assert parse_amount("3000") == Decimal(3000)
    assert parse_amount("  2 500 ") == Decimal(2500)
    assert parse_amount("много") is None


def test_a_word_unrelated_to_money_does_not_become_a_category() -> None:
    # "такси" shares no letters with "Транспорт": the bot asks rather than guesses.
    parsed = parse_expense("такси 350", CATEGORIES)
    assert parsed is not None and parsed.category_id is None and parsed.comment == "такси"
