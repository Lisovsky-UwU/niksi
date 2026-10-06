import logging

import httpx

from app.interfaces.services import NotificationService

log = logging.getLogger(__name__)


class TelegramNotifier(NotificationService):
    """Posts plain messages through the Bot API. Without a token it quietly does nothing,
    so the web app keeps working when the bot is not set up."""

    def __init__(self, token: str | None, api_url: str = "https://api.telegram.org") -> None:
        self._token = token
        self._api_url = api_url.rstrip("/")

    def send(self, chat_id: int, text: str) -> None:
        if not self._token:
            return
        try:
            httpx.post(
                f"{self._api_url}/bot{self._token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
                timeout=5,
            )
        except httpx.HTTPError:
            log.warning("Telegram notification to chat %s failed", chat_id, exc_info=True)
