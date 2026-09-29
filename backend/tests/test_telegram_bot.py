from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_notification_service
from app.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.infrastructure.security import Argon2PasswordHasher
from app.interfaces.services import NotificationService
from app.telegram.service import BotService

NIK_TG, PAIR_TG, STRANGER_TG = 111, 222, 999
CHAT = -1001
NOW = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)


def _seed_user(client: TestClient, email: str, password: str, name: str) -> int:
    db = client.app.state.testing_session_local()
    try:
        return SqlAlchemyUserRepository(db).create(email, Argon2PasswordHasher().hash(password), name).id
    finally:
        db.close()


def _login(client: TestClient, email: str, password: str) -> None:
    assert client.post("/api/auth/login", json={"email": email, "password": password}).status_code == 200


class FakeNotifier(NotificationService):
    def __init__(self) -> None:
        self.sent: list[tuple[int, str]] = []

    def send(self, chat_id: int, text: str) -> None:
        self.sent.append((chat_id, text))


@pytest.fixture()
def bot(client: TestClient):  # type: ignore[no-untyped-def]
    """Two linked people, September with categories, and a way to talk to the bot."""
    ids = {
        "nik": _seed_user(client, "nik@example.com", "pw-nik", "Ник"),
        "pair": _seed_user(client, "pair@example.com", "pw-pair", "Сюса"),
    }
    _login(client, "nik@example.com", "pw-nik")
    month = client.post("/api/months", json={"year": 2026, "month": 9, "start_date": "2026-09-01"})
    month_id = month.json()["id"]
    cats = {}
    for name, limit in (("Продукты", "10000"), ("Кафе и доставка", "3000"), ("Дом и быт", "8000")):
        cats[name] = client.post(
            f"/api/months/{month_id}/categories", json={"name": name, "limit_amount": limit}
        ).json()["id"]

    def service(now: datetime = NOW) -> BotService:
        return BotService(client.app.state.testing_session_local(), now)

    def link(email: str, password: str, tg_id: int) -> None:
        _login(client, email, password)
        code = client.post("/api/users/me/telegram-code").json()["code"]
        assert "Готово" in service().link(tg_id, code).text

    link("pair@example.com", "pw-pair", PAIR_TG)
    link("nik@example.com", "pw-nik", NIK_TG)  # stays logged in as Nik
    return {"service": service, "ids": ids, "cats": cats, "month_id": month_id}


def _expenses(client: TestClient, month_id: int) -> list[dict]:
    return client.get("/api/expenses", params={"month_id": month_id}).json()


def test_linking_with_a_code_from_the_settings(client: TestClient, bot) -> None:  # type: ignore[no-untyped-def]
    assert client.get("/api/auth/me").json()["telegram_linked"] is True
    service = bot["service"]
    assert "не знаю" in service().left(STRANGER_TG).text
    assert "не подошёл" in service().link(STRANGER_TG, "000000").text

    # A code lives for 15 minutes.
    code = client.post("/api/users/me/telegram-code").json()["code"]
    later = datetime.now(UTC) + timedelta(minutes=16)
    assert "не подошёл" in service(later).link(STRANGER_TG, code).text

    assert client.delete("/api/users/me/telegram").json()["telegram_linked"] is False
    assert "не знаю" in service().left(NIK_TG).text


def test_expense_lines_are_recorded_for_whoever_wrote_them(client: TestClient, bot) -> None:  # type: ignore[no-untyped-def]
    service = bot["service"]
    reply = service().message(NIK_TG, "450 прод пятёрочка у дома")
    assert reply is not None
    assert "Ник" in reply.text and "450" in reply.text and "Продукты" in reply.text
    assert "<blockquote>пятёрочка у дома</blockquote>" in reply.text
    assert [b.text for b in reply.buttons[0]] == ["↩️ Отменить", "🔀 Другая категория"]

    service().message(PAIR_TG, "кафе\n500\nакадемия кофе")
    expenses = _expenses(client, bot["month_id"])
    by_amount = {e["amount"]: e for e in expenses}
    assert by_amount["500.00"]["spent_by_user_id"] == bot["ids"]["pair"]
    assert by_amount["500.00"]["description"] == "академия кофе"
    assert by_amount["450.00"]["category_id"] == bot["cats"]["Продукты"]

    # Ordinary chat stays unanswered.
    assert service().message(NIK_TG, "буду дома в 19") is None
    assert len(_expenses(client, bot["month_id"])) == 2


def test_unknown_category_is_picked_with_buttons(client: TestClient, bot) -> None:  # type: ignore[no-untyped-def]
    service = bot["service"]
    ask = service().message(PAIR_TG, "700 шаверма")
    assert ask is not None and "В какую категорию" in ask.text
    cafe = next(b for row in ask.buttons for b in row if b.text == "Кафе и доставка")
    done = service().callback(NIK_TG, cafe.data)
    assert done is not None and "Кафе и доставка" in done.text
    [expense] = _expenses(client, bot["month_id"])
    # Whoever presses the button, the expense belongs to the one who wrote the message.
    assert expense["spent_by_user_id"] == bot["ids"]["pair"]
    assert expense["description"] == "шаверма"
    # The button works once.
    assert "устарела" in service().callback(NIK_TG, cafe.data).text

    drop = service().message(NIK_TG, "300")
    assert drop is not None
    assert "не записываю" in service().callback(NIK_TG, drop.buttons[-1][0].data).text
    assert len(_expenses(client, bot["month_id"])) == 1


def test_undo_and_another_category_buttons(client: TestClient, bot) -> None:  # type: ignore[no-untyped-def]
    service = bot["service"]
    reply = service().message(NIK_TG, "1500 дом и быт за электричество")
    assert reply is not None
    undo, recat = reply.buttons[0]

    choose = service().callback(NIK_TG, recat.data)
    assert choose is not None
    food = next(b for row in choose.buttons for b in row if b.text == "Продукты")
    moved = service().callback(NIK_TG, food.data)
    assert moved is not None and "Продукты" in moved.text
    assert _expenses(client, bot["month_id"])[0]["category_id"] == bot["cats"]["Продукты"]

    assert "Трата отменена" in service().callback(NIK_TG, undo.data).text
    assert _expenses(client, bot["month_id"]) == []
    assert "уже удалена" in service().callback(NIK_TG, undo.data).text


def test_undo_command_removes_only_my_last_expense(client: TestClient, bot) -> None:  # type: ignore[no-untyped-def]
    service = bot["service"]
    service().message(NIK_TG, "100 прод")
    service().message(NIK_TG, "200 прод")
    service().message(PAIR_TG, "300 прод")
    assert "200" in service().undo(NIK_TG).text
    assert sorted(e["amount"] for e in _expenses(client, bot["month_id"])) == ["100.00", "300.00"]


def test_limit_warnings_appear_once_per_line(client: TestClient, bot) -> None:  # type: ignore[no-untyped-def]
    service = bot["service"]
    first = service().message(NIK_TG, "2000 кафе")
    assert first is not None and "⚠️" not in first.text
    close = service().message(NIK_TG, "500 кафе")  # 2500 of 3000: past 80%
    assert close is not None and "80%" in close.text
    quiet = service().message(NIK_TG, "100 кафе")
    assert quiet is not None and "⚠️" not in quiet.text and "🔴" not in quiet.text
    over = service().message(NIK_TG, "1000 кафе")
    assert over is not None and "перерасход" in over.text


def test_views_of_the_month(client: TestClient, bot) -> None:  # type: ignore[no-untyped-def]
    service = bot["service"]
    service().message(NIK_TG, "2500 кафе ужин")
    service().message(NIK_TG, "+40000 аванс")

    left = service().left(NIK_TG).text
    assert "Сентябрь 2026" in left and "Осталось" in left and "в день" in left
    cats = service().cats(PAIR_TG).text
    assert "Кафе и доставка" in cats and "🟡" in cats
    month = service().month(NIK_TG).text
    assert "Доходы" in month and "Остаток" in month and "<pre>" in month
    last = service().last(NIK_TG).text
    assert "ужин" in last and "Ник" in last


def test_income_and_grey_zone(client: TestClient, bot) -> None:  # type: ignore[no-untyped-def]
    service = bot["service"]
    income = service().message(PAIR_TG, "+45 000 зарплата")
    assert income is not None and "Доход записан" in income.text
    entries = client.get(f"/api/months/{bot['month_id']}/income/entries").json()
    assert entries[0]["user_id"] == bot["ids"]["pair"] and entries[0]["description"] == "зарплата"

    assert "Сколько взяли" in service().grey(NIK_TG, "").text
    grey = service().grey(NIK_TG, "3000")
    assert "3" in grey.text and "Серая зона" in grey.text
    assert client.get(f"/api/months/{bot['month_id']}/grey-zone").json()["entries"][0]["amount"] == "3000.00"


def test_shared_chat_notifications_and_evening_summary(client: TestClient, bot) -> None:  # type: ignore[no-untyped-def]
    service = bot["service"]
    fake = FakeNotifier()
    client.app.dependency_overrides[get_notification_service] = lambda: fake
    try:
        # Without a bound chat the web app notifies nobody.
        client.post(
            "/api/expenses",
            json={"category_id": bot["cats"]["Продукты"], "amount": "100", "expense_date": "2026-09-20"},
        )
        assert fake.sent == []

        assert "беседа теперь общая" in service().bind(NIK_TG, CHAT, is_private=False).text
        assert service().chat_allowed(CHAT, is_private=False)
        assert not service().chat_allowed(-2002, is_private=False)
        assert service().chat_allowed(NIK_TG, is_private=True)

        client.post(
            "/api/expenses",
            json={
                "category_id": bot["cats"]["Продукты"],
                "amount": "8000",
                "expense_date": "2026-09-20",
                "description": "закупка на месяц",
                "spent_by_user_id": bot["ids"]["pair"],
            },
        )
        [(chat_id, text)] = fake.sent
        assert chat_id == CHAT
        assert "Сюса" in text and "8" in text and "закупка на месяц" in text and "80%" in text

        assert "выключены" in service().set_flag("notify", "off").text
        client.post(
            "/api/expenses",
            json={"category_id": bot["cats"]["Продукты"], "amount": "10", "expense_date": "2026-09-20"},
        )
        assert len(fake.sent) == 1
    finally:
        client.app.dependency_overrides.pop(get_notification_service, None)

    summary = service().daily_summary()
    assert summary is not None
    chat_id, text = summary
    assert chat_id == CHAT and "Итоги дня" in text and "Осталось" in text
    # Once a day.
    assert service().daily_summary() is None
    assert service(NOW + timedelta(days=1)).daily_summary() is not None
