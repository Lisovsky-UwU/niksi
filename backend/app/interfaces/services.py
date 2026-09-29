"""Abstract technical-service contracts (as opposed to data-access repositories).

`PasswordHasher` and `TokenService` back the auth use cases; `NotificationService`
delivers messages to the couple's Telegram chat (e.g. when a partner logs an expense
in the web app).
"""

from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, plain_password: str) -> str: ...

    @abstractmethod
    def verify(self, plain_password: str, password_hash: str) -> bool: ...


class TokenService(ABC):
    @abstractmethod
    def create_token(self, user_id: int) -> str: ...

    @abstractmethod
    def decode_token(self, token: str) -> int:
        """Return the user id encoded in the token, or raise AuthenticationError."""
        ...


class NotificationService(ABC):
    @abstractmethod
    def send(self, chat_id: int, text: str) -> None:
        """Deliver a message; failures are swallowed, a notification is never worth an error."""
        ...
