from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://niksi:niksi@localhost:5432/niksi"

    secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_days: int = 30
    cookie_secure: bool = True

    seed_user1_email: str | None = None
    seed_user1_password: str | None = None
    seed_user1_name: str | None = None
    seed_user2_email: str | None = None
    seed_user2_password: str | None = None
    seed_user2_name: str | None = None


settings = Settings()
