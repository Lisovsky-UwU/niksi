"""Idempotent seed for the two household accounts.

Run with:  python -m app.scripts.seed_users
Reads SEED_USER1_{EMAIL,PASSWORD,NAME} / SEED_USER2_{EMAIL,PASSWORD,NAME} from env/.env.
Never overwrites an existing account.
"""

from app.core.config import settings
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.infrastructure.security import Argon2PasswordHasher


def seed() -> None:
    hasher = Argon2PasswordHasher()
    accounts = [
        (settings.seed_user1_email, settings.seed_user1_password, settings.seed_user1_name),
        (settings.seed_user2_email, settings.seed_user2_password, settings.seed_user2_name),
    ]
    with SessionLocal() as db:
        repo = SqlAlchemyUserRepository(db)
        for email, password, name in accounts:
            if not email or not password or not name:
                print(f"Skipping incomplete seed account config for {email!r}")
                continue
            if repo.get_credentials_by_email(email) is not None:
                print(f"User {email} already exists, skipping")
                continue
            repo.create(email=email, password_hash=hasher.hash(password), display_name=name)
            print(f"Created user {email}")


if __name__ == "__main__":
    seed()
