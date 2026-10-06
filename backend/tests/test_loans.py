from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.domain.loans import forecast, nth_payment_date, split_regular
from app.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.infrastructure.security import Argon2PasswordHasher


def test_payment_dates_follow_the_number_of_payments() -> None:
    assert nth_payment_date(date(2026, 9, 1), 15, 1) == date(2026, 9, 15)
    assert nth_payment_date(date(2026, 9, 15), 15, 1) == date(2026, 10, 15)
    assert nth_payment_date(date(2026, 9, 1), 15, 4) == date(2026, 12, 15)
    # The 31st falls on the last day of shorter months, and comes back after them.
    assert nth_payment_date(date(2026, 1, 31), 31, 1) == date(2026, 2, 28)
    assert nth_payment_date(date(2026, 1, 31), 31, 2) == date(2026, 3, 31)
    assert nth_payment_date(date(2026, 11, 20), 5, 2) == date(2027, 1, 5)


def test_regular_payment_split_and_forecast() -> None:
    assert split_regular(Decimal("100000"), Decimal("12"), Decimal("10000")) == (Decimal("1000.00"), Decimal("9000.00"))
    # A payment smaller than the interest goes to interest only.
    assert split_regular(Decimal("100000"), Decimal("12"), Decimal("600")) == (Decimal("600"), Decimal("0"))

    result = forecast(Decimal("1000"), Decimal("12"), Decimal("1000"))
    assert result is not None
    assert (result.payments_left, result.interest_left) == (2, Decimal("10.10"))

    no_rate = forecast(Decimal("1000"), Decimal("0"), Decimal("300"))
    assert no_rate is not None and (no_rate.payments_left, no_rate.interest_left) == (4, Decimal(0))

    assert forecast(Decimal("100000"), Decimal("12"), Decimal("1000")) is None
    assert forecast(Decimal("0"), Decimal("12"), Decimal("1000")) == forecast(Decimal("-1"), Decimal("1"), Decimal("1"))


@pytest.fixture()
def logged_in(client: TestClient) -> None:
    db = client.app.state.testing_session_local()
    try:
        SqlAlchemyUserRepository(db).create("nik@example.com", Argon2PasswordHasher().hash("pw"), "Ник")
    finally:
        db.close()
    assert client.post("/api/auth/login", json={"email": "nik@example.com", "password": "pw"}).status_code == 200


def _loan(client: TestClient, **fields: str | int) -> dict:
    payload = {
        "name": "Потребкредит",
        "principal": "100000",
        "start_date": "2026-09-01",
        "rate_percent": "12",
        "monthly_payment": "10000",
        "payment_day": 15,
    } | fields
    resp = client.post("/api/loans", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _pay(client: TestClient, loan_id: int, **fields: str) -> dict:
    resp = client.post(f"/api/loans/{loan_id}/payments", json=fields)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _get(client: TestClient, loan_id: int) -> dict:
    return next(loan for loan in client.get("/api/loans").json() if loan["id"] == loan_id)


def test_loan_payments_reduce_the_balance(client: TestClient, logged_in: None) -> None:
    loan = _loan(client)
    assert loan["balance"] == "100000.00"
    assert loan["next_payment_date"] == "2026-09-15"
    assert loan["payments_left"] == 11
    assert loan["payoff_date"] == "2027-07-15"
    assert "last_reminded_due" not in loan

    regular = _pay(client, loan["id"], kind="regular", amount="10000", payment_date="2026-09-14")
    assert (regular["interest_part"], regular["principal_part"]) == ("1000.00", "9000.00")
    loan = _get(client, loan["id"])
    assert loan["balance"] == "91000.00"
    assert loan["next_payment_date"] == "2026-10-15"

    early = _pay(client, loan["id"], kind="early", amount="1000", payment_date="2026-09-20")
    assert (early["interest_part"], early["principal_part"]) == ("0.00", "1000.00")
    correction = _pay(client, loan["id"], kind="correction", new_balance="89500", payment_date="2026-09-21")
    assert (correction["amount"], correction["principal_part"]) == ("0.00", "500.00")
    loan = _get(client, loan["id"])
    assert loan["balance"] == "89500.00"
    # Neither an early repayment nor a correction counts as the month's regular payment.
    assert loan["next_payment_date"] == "2026-10-15"

    too_much = {"kind": "early", "amount": "90000", "payment_date": "2026-09-22"}
    assert client.post(f"/api/loans/{loan['id']}/payments", json=too_much).status_code == 409
    no_amount = {"kind": "regular", "payment_date": "2026-09-22"}
    assert client.post(f"/api/loans/{loan['id']}/payments", json=no_amount).status_code == 409

    payments = client.get(f"/api/loans/{loan['id']}/payments").json()
    assert [p["kind"] for p in payments] == ["correction", "early", "regular"]

    assert client.delete(f"/api/loans/payments/{early['id']}").status_code == 204
    assert _get(client, loan["id"])["balance"] == "90500.00"


def test_loan_payments_leave_the_month_budget(client: TestClient, logged_in: None) -> None:
    month_id = client.post("/api/months", json={"year": 2026, "month": 9, "start_date": "2026-09-01"}).json()["id"]
    client.post(
        f"/api/months/{month_id}/income/entries",
        json={"amount": "100000", "received_date": "2026-09-05"},
    )
    client.post("/api/reconciliations", json={"actual_balance": "0", "balance_date": "2026-09-01"})

    loan = _loan(client)
    _pay(client, loan["id"], kind="regular", amount="10000", payment_date="2026-09-15")
    _pay(client, loan["id"], kind="early", amount="5000", payment_date="2026-09-16")
    _pay(client, loan["id"], kind="correction", new_balance="80000", payment_date="2026-09-17")

    balance = client.get(f"/api/months/{month_id}/summary").json()["balance"]
    assert balance["loan_payments"] == "15000.00"
    assert balance["net"] == "85000.00"

    status = client.get("/api/balance").json()
    assert status["flows_since"]["loan_payments"] == "15000.00"
    assert status["expected_now"] == "85000.00"


def test_closing_and_deleting_loans(client: TestClient, logged_in: None) -> None:
    empty = _loan(client, name="Рассрочка", rate_percent="0", principal="30000", monthly_payment="5000", payment_day=31)
    assert empty["next_payment_date"] == "2026-09-30"
    assert empty["interest_left"] == "0.00"
    assert client.delete(f"/api/loans/{empty['id']}").status_code == 204

    loan = _loan(client)
    _pay(client, loan["id"], kind="regular", amount="10000", payment_date="2026-09-15")
    assert client.delete(f"/api/loans/{loan['id']}").status_code == 409

    update = {
        "name": "Потреб",
        "principal": "100000",
        "start_date": "2026-09-01",
        "rate_percent": "12",
        "monthly_payment": "10000",
        "payment_day": 15,
        "is_closed": True,
    }
    closed = client.put(f"/api/loans/{loan['id']}", json=update).json()
    assert closed["is_closed"] is True and closed["next_payment_date"] is None
    payment = {"kind": "regular", "amount": "10000", "payment_date": "2026-10-15"}
    assert client.post(f"/api/loans/{loan['id']}/payments", json=payment).status_code == 409
