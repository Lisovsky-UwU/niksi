from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://niksi:niksi@localhost:5432/niksi"

    secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_days: int = 30
    cookie_secure: bool = True

    # Telegram bot (optional): token from @BotFather, when the evening summary and loan
    # payment reminders are sent and in which timezone that time is. The API URL can point to a mirror/proxy or a local
    # telegram-bot-api server when api.telegram.org is unreachable.
    telegram_bot_token: str | None = None
    telegram_api_url: str = "https://api.telegram.org"
    telegram_bot_username: str | None = None
    telegram_summary_time: str = "21:00"
    telegram_reminder_time: str = "10:00"
    telegram_timezone: str = "Europe/Moscow"

    seed_user1_email: str | None = None
    seed_user1_password: str | None = None
    seed_user1_name: str | None = None
    seed_user2_email: str | None = None
    seed_user2_password: str | None = None
    seed_user2_name: str | None = None


settings = Settings()
