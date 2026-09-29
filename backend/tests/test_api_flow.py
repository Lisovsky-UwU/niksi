from fastapi.testclient import TestClient

from app.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.infrastructure.security import Argon2PasswordHasher


def _seed_user(client: TestClient, email: str, password: str, name: str) -> None:
    db = client.app.state.testing_session_local()
    try:
        repo = SqlAlchemyUserRepository(db)
        hasher = Argon2PasswordHasher()
        repo.create(email=email, password_hash=hasher.hash(password), display_name=name)
    finally:
        db.close()


def test_full_budget_flow(client: TestClient) -> None:
    _seed_user(client, "nikita@example.com", "hunter2", "Никита")
    _seed_user(client, "girlfriend@example.com", "correcthorse", "Девушка")

    unauthenticated_me = client.get("/api/auth/me")
    assert unauthenticated_me.status_code == 401

    bad_login = client.post("/api/auth/login", json={"email": "nikita@example.com", "password": "wrong"})
    assert bad_login.status_code == 401

    login_resp = client.post("/api/auth/login", json={"email": "nikita@example.com", "password": "hunter2"})
    assert login_resp.status_code == 200
    assert login_resp.json()["display_name"] == "Никита"
    assert "access_token" in client.cookies

    me_resp = client.get("/api/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "nikita@example.com"

    month_resp = client.post("/api/months", json={"year": 2026, "month": 9})
    assert month_resp.status_code == 201
    month_id = month_resp.json()["id"]

    duplicate_month_resp = client.post("/api/months", json={"year": 2026, "month": 9})
    assert duplicate_month_resp.status_code == 409

    get_month_resp = client.get("/api/months/2026/9")
    assert get_month_resp.status_code == 200
    assert get_month_resp.json()["id"] == month_id

    missing_month_resp = client.get("/api/months/2025/1")
    assert missing_month_resp.status_code == 404

    category_resp = client.post(
        f"/api/months/{month_id}/categories", json={"name": "Продукты", "limit_amount": "30000"}
    )
    assert category_resp.status_code == 201
    category_id = category_resp.json()["id"]

    client.post(f"/api/months/{month_id}/categories", json={"name": "Квартира", "limit_amount": "50000"})

    categories_resp = client.get(f"/api/months/{month_id}/categories")
    assert categories_resp.status_code == 200
    assert len(categories_resp.json()) == 2

    expense_resp = client.post(
        "/api/expenses",
        json={"category_id": category_id, "amount": "1500.50", "expense_date": "2026-09-05"},
    )
    assert expense_resp.status_code == 201

    client.post(
        "/api/expenses",
        json={"category_id": category_id, "amount": "300", "description": "кофе", "expense_date": "2026-09-06"},
    )

    expenses_resp = client.get("/api/expenses", params={"month_id": month_id})
    assert expenses_resp.status_code == 200
    assert len(expenses_resp.json()) == 2

    income_resp = client.put(
        f"/api/months/{month_id}/income/me",
        json={"forecast_amount": "150000", "actual_amount": "148000"},
    )
    assert income_resp.status_code == 200

    summary_resp = client.get(f"/api/months/{month_id}/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    groceries = next(c for c in summary["categories"] if c["id"] == category_id)
    assert groceries["spent"] == "1800.50"
    assert groceries["remaining"] == "28199.50"
    assert summary["totals"]["total_spent"] == "1800.50"
    assert summary["income"]["household_actual"] == "148000.00"
    assert summary["balance"]["net"] == "146199.50"

    # Second month, copying categories from the first
    second_month_resp = client.post(
        "/api/months",
        json={"year": 2026, "month": 10, "copy_categories_from_previous": True},
    )
    assert second_month_resp.status_code == 201
    second_month_id = second_month_resp.json()["id"]
    second_categories_resp = client.get(f"/api/months/{second_month_id}/categories")
    assert {c["name"] for c in second_categories_resp.json()} == {"Продукты", "Квартира"}

    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401
