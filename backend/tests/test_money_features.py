from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.infrastructure.security import Argon2PasswordHasher


def _seed_user(client: TestClient, email: str, password: str, name: str) -> int:
    db = client.app.state.testing_session_local()
    try:
        repo = SqlAlchemyUserRepository(db)
        return repo.create(email=email, password_hash=Argon2PasswordHasher().hash(password), display_name=name).id
    finally:
        db.close()


def _login(client: TestClient, email: str, password: str) -> None:
    assert client.post("/api/auth/login", json={"email": email, "password": password}).status_code == 200


@pytest.fixture()
def couple(client: TestClient) -> dict[str, int]:
    nik = _seed_user(client, "nik@example.com", "pw-nik", "Ник")
    pair = _seed_user(client, "pair@example.com", "pw-pair", "Половинка")
    _login(client, "nik@example.com", "pw-nik")
    return {"nik": nik, "pair": pair}


def _month(client: TestClient, year: int, month: int, copy: bool = False) -> int:
    resp = client.post("/api/months", json={"year": year, "month": month, "copy_categories_from_previous": copy})
    assert resp.status_code == 201
    return resp.json()["id"]


def _category(client: TestClient, month_id: int, name: str, limit: str) -> int:
    return client.post(f"/api/months/{month_id}/categories", json={"name": name, "limit_amount": limit}).json()["id"]


def _expense(client: TestClient, category_id: int, amount: str, day: str) -> None:
    resp = client.post("/api/expenses", json={"category_id": category_id, "amount": amount, "expense_date": day})
    assert resp.status_code == 201


def _summary(client: TestClient, month_id: int) -> dict:
    resp = client.get(f"/api/months/{month_id}/summary")
    assert resp.status_code == 200
    return resp.json()


def test_income_is_expected_plan_plus_actual_entries(client: TestClient, couple: dict[str, int]) -> None:
    month_id = _month(client, 2026, 9)
    client.put(f"/api/months/{month_id}/income/me", json={"forecast_amount": "90000"})

    advance = client.post(
        f"/api/months/{month_id}/income/entries",
        json={"amount": "40000", "description": "Аванс", "received_date": "2026-09-15"},
    )
    assert advance.status_code == 201
    # Recording the partner's salary on their behalf.
    partner_salary = client.post(
        f"/api/months/{month_id}/income/entries",
        json={"amount": "70000", "received_date": "2026-09-05", "user_id": couple["pair"]},
    )
    assert partner_salary.json()["user_id"] == couple["pair"]
    assert partner_salary.json()["created_by_user_id"] == couple["nik"]

    entries = client.get(f"/api/months/{month_id}/income/entries").json()
    assert [e["amount"] for e in entries] == ["40000.00", "70000.00"]  # newest first

    income = _summary(client, month_id)["income"]
    by_user = {u["user_id"]: u for u in income["per_user"]}
    assert by_user[couple["nik"]]["forecast"] == "90000.00"
    assert by_user[couple["nik"]]["actual"] == "40000.00"
    # The partner appears even without a forecast of their own.
    assert by_user[couple["pair"]]["forecast"] == "0"
    assert by_user[couple["pair"]]["actual"] == "70000.00"
    assert income["household_actual"] == "110000.00"

    assert client.delete(f"/api/income-entries/{advance.json()['id']}").status_code == 204
    assert _summary(client, month_id)["income"]["household_actual"] == "70000.00"


def test_grey_zone_is_visible_to_both_but_managed_by_its_owner(client: TestClient, couple: dict[str, int]) -> None:
    month_id = _month(client, 2026, 9)
    client.post(f"/api/months/{month_id}/income/entries", json={"amount": "100000", "received_date": "2026-09-01"})

    assert client.put(f"/api/months/{month_id}/grey-zone/me", json={"amount": "10000"}).status_code == 200
    first = client.post(f"/api/months/{month_id}/grey-zone/entries", json={"amount": "3000", "taken_date": "2026-09-02"})
    client.post(f"/api/months/{month_id}/grey-zone/entries", json={"amount": "4000", "taken_date": "2026-09-12"})

    summary = _summary(client, month_id)
    nik = next(u for u in summary["grey_zone"]["per_user"] if u["user_id"] == couple["nik"])
    assert (nik["limit"], nik["taken"], nik["remaining"]) == ("10000.00", "7000.00", "3000.00")
    assert summary["balance"]["grey_zone_taken"] == "7000.00"
    assert summary["balance"]["net"] == "93000.00"

    # The partner sees the numbers but cannot remove Nik's record.
    client.post("/api/auth/logout")
    _login(client, "pair@example.com", "pw-pair")
    assert len(client.get(f"/api/months/{month_id}/grey-zone").json()["entries"]) == 2
    assert client.delete(f"/api/grey-zone/entries/{first.json()['id']}").status_code == 403


def test_savings_pots_and_goals(client: TestClient, couple: dict[str, int]) -> None:
    month_id = _month(client, 2026, 9)
    client.post(f"/api/months/{month_id}/income/entries", json={"amount": "100000", "received_date": "2026-09-01"})

    assert client.post("/api/savings/pots", json={"name": "Шкаф", "kind": "goal"}).status_code == 409
    goal = client.post(
        "/api/savings/pots",
        json={"name": "Шкаф", "kind": "goal", "target_amount": "60000", "target_date": "2027-03-01"},
    ).json()
    deposit = client.post("/api/savings/pots", json={"name": "Вклад", "kind": "deposit"}).json()

    def transfer(pot_id: int, direction: str, amount: str, day: str = "2026-09-20") -> int:
        resp = client.post(
            f"/api/savings/pots/{pot_id}/transfers",
            json={"direction": direction, "amount": amount, "transfer_date": day},
        )
        return resp.status_code

    assert transfer(goal["id"], "in", "15000") == 201
    assert transfer(deposit["id"], "in", "20000") == 201
    assert transfer(deposit["id"], "interest", "300") == 201
    assert transfer(goal["id"], "out", "5000") == 201
    assert transfer(goal["id"], "out", "999999") == 409

    pots = {p["name"]: p for p in client.get("/api/savings/pots").json()}
    assert pots["Шкаф"]["balance"] == "10000.00"
    assert pots["Вклад"]["balance"] == "20300.00"

    # Interest grows the pot but is not money taken out of the budget.
    balance = _summary(client, month_id)["balance"]
    assert balance["savings_net"] == "30000.00"
    assert balance["net"] == "70000.00"

    assert client.delete(f"/api/savings/pots/{goal['id']}").status_code == 409
    archived = client.put(
        f"/api/savings/pots/{goal['id']}",
        json={"name": "Шкаф", "target_amount": "60000", "target_date": "2027-03-01", "is_archived": True},
    )
    assert archived.status_code == 200
    assert [p["name"] for p in client.get("/api/savings/pots").json()] == ["Вклад"]
    assert len(client.get("/api/savings/pots", params={"include_archived": True}).json()) == 2


def test_reconciliation_compares_real_money_with_records(client: TestClient, couple: dict[str, int]) -> None:
    month_id = _month(client, 2026, 9)
    food = _category(client, month_id, "Продукты", "30000")

    status = client.get("/api/balance").json()
    assert status["last_reconciliation"] is None and status["expected_now"] is None

    first = client.post("/api/reconciliations", json={"actual_balance": "50000", "balance_date": "2026-09-01"})
    assert first.json()["expected_balance"] is None
    assert first.json()["difference"] == "0.00"

    client.post(f"/api/months/{month_id}/income/entries", json={"amount": "40000", "received_date": "2026-09-05"})
    _expense(client, food, "12000", "2026-09-06")
    client.post(f"/api/months/{month_id}/grey-zone/entries", json={"amount": "5000", "taken_date": "2026-09-07"})
    pot = client.post("/api/savings/pots", json={"name": "Подушка", "kind": "account"}).json()
    client.post(
        f"/api/savings/pots/{pot['id']}/transfers",
        json={"direction": "in", "amount": "10000", "transfer_date": "2026-09-08"},
    )

    # 50000 + 40000 - 12000 - 5000 - 10000
    status = client.get("/api/balance").json()
    assert status["expected_now"] == "63000.00"
    assert status["flows_since"]["expenses"] == "12000.00"

    # In reality there is 60 500 — 2 500 went somewhere unrecorded.
    second = client.post(
        "/api/reconciliations", json={"actual_balance": "60500", "balance_date": "2026-09-10", "note": "по картам"}
    ).json()
    assert second["expected_balance"] == "63000.00"
    assert second["difference"] == "-2500.00"
    assert client.get("/api/balance").json()["expected_now"] == "60500.00"
    assert _summary(client, month_id)["balance"]["adjustments"] == "-2500.00"

    assert (
        client.post("/api/reconciliations", json={"actual_balance": "1", "balance_date": "2026-09-09"}).status_code
        == 409
    )
    assert client.delete(f"/api/reconciliations/{first.json()['id']}").status_code == 409
    assert client.delete(f"/api/reconciliations/{second['id']}").status_code == 204
    assert client.get("/api/balance").json()["expected_now"] == "63000.00"


def test_leftover_carries_over_to_next_month(client: TestClient, couple: dict[str, int]) -> None:
    august = _month(client, 2026, 8)
    client.put(f"/api/months/{august}/income/me", json={"forecast_amount": "90000"})
    client.put(f"/api/months/{august}/grey-zone/me", json={"amount": "8000"})
    rent = _category(client, august, "Квартира", "50000")
    client.post(f"/api/months/{august}/income/entries", json={"amount": "90000", "received_date": "2026-08-05"})
    _expense(client, rent, "50000", "2026-08-06")

    # A starting balance from before the app was used.
    assert client.put(f"/api/months/{august}/carryover", json={"amount": "15000"}).status_code == 200
    aug = _summary(client, august)["carryover"]
    assert aug == {"carried_over": "15000.00", "is_manual": True, "closing": "55000.00"}

    september = _month(client, 2026, 9, copy=True)
    sep = _summary(client, september)
    assert sep["carryover"]["carried_over"] == "55000.00"
    assert sep["carryover"]["is_manual"] is False
    # Plans travel with "copy from previous": expected income and the grey zone limit.
    nik_income = next(u for u in sep["income"]["per_user"] if u["user_id"] == couple["nik"])
    nik_grey = next(u for u in sep["grey_zone"]["per_user"] if u["user_id"] == couple["nik"])
    assert (nik_income["forecast"], nik_income["actual"]) == ("90000.00", "0")
    assert nik_grey["limit"] == "8000.00"

    # Changing August ripples into September's carry-over.
    client.post(f"/api/months/{august}/income/entries", json={"amount": "1000", "received_date": "2026-08-20"})
    assert _summary(client, september)["carryover"]["carried_over"] == "56000.00"

    assert client.put(f"/api/months/{september}/carryover", json={"amount": "50000"}).status_code == 200
    assert Decimal(_summary(client, september)["carryover"]["carried_over"]) == Decimal(50000)
    client.put(f"/api/months/{september}/carryover", json={"amount": None})
    assert _summary(client, september)["carryover"]["is_manual"] is False


def test_users_are_listed_for_both_partners(client: TestClient, couple: dict[str, int]) -> None:
    users = client.get("/api/users").json()
    assert [u["display_name"] for u in users] == ["Ник", "Половинка"]


def test_category_colour_is_chosen_by_hand_and_travels_to_the_next_month(
    client: TestClient, couple: dict[str, int]
) -> None:
    august = _month(client, 2026, 8)
    food = client.post(
        f"/api/months/{august}/categories", json={"name": "Продукты", "limit_amount": "30000", "color": "teal"}
    ).json()
    fun = _category(client, august, "Развлечения", "10000")
    assert food["color"] == "teal"
    assert client.get(f"/api/months/{august}/categories").json()[1]["color"] is None

    assert client.put(f"/api/categories/{fun}", json={"color": "lilac"}).json()["color"] == "lilac"
    # Other fields leave the colour alone; "auto" hands it back to automatic.
    assert client.put(f"/api/categories/{fun}", json={"limit_amount": "12000"}).json()["color"] == "lilac"
    assert client.put(f"/api/categories/{food['id']}", json={"color": "auto"}).json()["color"] is None
    assert client.put(f"/api/categories/{fun}", json={"color": "red"}).status_code == 422

    september = _month(client, 2026, 9, copy=True)
    colours = {c["name"]: c["color"] for c in client.get(f"/api/months/{september}/categories").json()}
    assert colours == {"Продукты": None, "Развлечения": "lilac"}


def test_profile_name_password_and_avatar(client: TestClient, couple: dict[str, int]) -> None:
    renamed = client.put("/api/users/me", json={"display_name": "  Никита  "})
    assert renamed.json()["display_name"] == "Никита"
    assert client.put("/api/users/me", json={"display_name": ""}).status_code == 422

    wrong = client.put("/api/users/me/password", json={"current_password": "nope", "new_password": "new-secret-1"})
    assert wrong.status_code == 409
    assert client.put("/api/users/me/password", json={"current_password": "pw-nik", "new_password": "short"}).status_code == 422
    changed = client.put("/api/users/me/password", json={"current_password": "pw-nik", "new_password": "new-secret-1"})
    assert changed.status_code == 204
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"email": "nik@example.com", "password": "pw-nik"}).status_code == 401
    _login(client, "nik@example.com", "new-secret-1")

    assert client.get("/api/auth/me").json()["avatar_version"] is None
    picture = b"RIFF\x00\x00\x00\x00WEBPVP8 fake-image-bytes"
    first = client.put("/api/users/me/avatar", content=picture, headers={"Content-Type": "image/webp"})
    assert first.json()["avatar_version"] == 1
    served = client.get(f"/api/users/{couple['nik']}/avatar")
    assert served.content == picture and served.headers["content-type"] == "image/webp"
    again = client.put("/api/users/me/avatar", content=picture, headers={"Content-Type": "image/png"})
    assert again.json()["avatar_version"] == 2

    too_big = client.put("/api/users/me/avatar", content=b"x" * (600 * 1024), headers={"Content-Type": "image/jpeg"})
    assert too_big.status_code == 409
    assert client.put("/api/users/me/avatar", content=b"<svg/>", headers={"Content-Type": "image/svg+xml"}).status_code == 409

    assert client.delete("/api/users/me/avatar").json()["avatar_version"] is None
    assert client.get(f"/api/users/{couple['nik']}/avatar").status_code == 404


def test_expense_can_be_edited_including_category_and_comment(client: TestClient, couple: dict[str, int]) -> None:
    september = _month(client, 2026, 9)
    food = _category(client, september, "Продукты", "30000")
    cafe = _category(client, september, "Кафе", "10000")
    expense = client.post(
        "/api/expenses",
        json={"category_id": food, "amount": "900", "description": "Пятёрочка", "expense_date": "2026-09-05"},
    ).json()

    edited = client.put(
        f"/api/expenses/{expense['id']}",
        json={"category_id": cafe, "amount": "1250.50", "description": "Ужин в грузинском, взяли хинкали"},
    ).json()
    assert (edited["category_id"], edited["amount"], edited["expense_date"]) == (cafe, "1250.50", "2026-09-05")
    assert edited["description"] == "Ужин в грузинском, взяли хинкали"

    # Leaving the comment out keeps it; sending null erases it.
    assert client.put(f"/api/expenses/{expense['id']}", json={"amount": "1300"}).json()["description"]
    assert client.put(f"/api/expenses/{expense['id']}", json={"description": None}).json()["description"] is None

    october = _month(client, 2026, 10)
    other_month = _category(client, october, "Продукты", "30000")
    assert client.put(f"/api/expenses/{expense['id']}", json={"category_id": other_month}).status_code == 409
    spent = {c["id"]: c["spent"] for c in _summary(client, september)["categories"]}
    assert spent == {food: "0", cafe: "1300.00"}


def test_copying_categories_twice_does_not_duplicate_them(client: TestClient, couple: dict[str, int]) -> None:
    august = _month(client, 2026, 8)
    _category(client, august, "Продукты", "30000")
    _category(client, august, "Кафе", "10000")
    september = _month(client, 2026, 9)
    _category(client, september, "продукты", "25000")  # added by hand, different case

    first = client.post(f"/api/months/{september}/categories/copy-from-previous").json()
    second = client.post(f"/api/months/{september}/categories/copy-from-previous").json()
    assert [c["name"] for c in first] == ["Кафе"]
    assert second == []
    names = sorted(c["name"] for c in client.get(f"/api/months/{september}/categories").json())
    assert names == ["Кафе", "продукты"]


def test_month_is_a_period_from_the_first_full_salary(client: TestClient, couple: dict[str, int]) -> None:
    september = client.post(
        "/api/months", json={"year": 2026, "month": 9, "start_date": "2026-09-05"}
    ).json()
    assert (september["start_date"], september["end_date"]) == ("2026-09-05", None)

    # October's salary came early, on 3 October; September now ends on 2 October.
    october = client.post("/api/months", json={"year": 2026, "month": 10, "start_date": "2026-10-03"}).json()
    months = {m["month"]: m for m in client.get("/api/months").json()}
    assert months[9]["end_date"] == "2026-10-02"
    assert months[10]["end_date"] is None

    # A start may be in the previous calendar month, but months stay in order.
    assert client.put(f"/api/months/{october['id']}/start", json={"start_date": "2026-09-28"}).status_code == 200
    assert client.get("/api/months/2026/9").json()["end_date"] == "2026-09-27"
    assert client.put(f"/api/months/{october['id']}/start", json={"start_date": "2026-09-05"}).status_code == 409
    assert client.put(f"/api/months/{october['id']}/start", json={"start_date": "2026-08-31"}).status_code == 409
    assert client.put(f"/api/months/{october['id']}/start", json={"start_date": "2026-11-01"}).status_code == 409
    assert client.post("/api/months", json={"year": 2026, "month": 11}).json()["start_date"] == "2026-11-01"

    # Savings moves and reconciliations are counted by period, not by calendar month.
    client.put(f"/api/months/{october['id']}/start", json={"start_date": "2026-10-03"})
    pot = client.post("/api/savings/pots", json={"name": "Вклад", "kind": "deposit"}).json()
    for day in ("2026-10-01", "2026-10-04"):
        client.post(
            f"/api/savings/pots/{pot['id']}/transfers",
            json={"direction": "in", "amount": "1000", "transfer_date": day},
        )
    assert _summary(client, september["id"])["balance"]["savings_net"] == "1000.00"
    assert _summary(client, october["id"])["balance"]["savings_net"] == "1000.00"


def test_expense_records_who_spent_the_money(client: TestClient, couple: dict[str, int]) -> None:
    september = _month(client, 2026, 9)
    food = _category(client, september, "Продукты", "30000")

    mine = client.post(
        "/api/expenses", json={"category_id": food, "amount": "500", "expense_date": "2026-09-05"}
    ).json()
    assert (mine["created_by_user_id"], mine["spent_by_user_id"]) == (couple["nik"], couple["nik"])

    # Nik writes down what the partner spent.
    theirs = client.post(
        "/api/expenses",
        json={"category_id": food, "amount": "700", "expense_date": "2026-09-05", "spent_by_user_id": couple["pair"]},
    ).json()
    assert (theirs["created_by_user_id"], theirs["spent_by_user_id"]) == (couple["nik"], couple["pair"])

    moved = client.put(f"/api/expenses/{mine['id']}", json={"spent_by_user_id": couple["pair"]}).json()
    assert moved["spent_by_user_id"] == couple["pair"]
    assert client.put(f"/api/expenses/{mine['id']}", json={"spent_by_user_id": 999}).status_code == 404
