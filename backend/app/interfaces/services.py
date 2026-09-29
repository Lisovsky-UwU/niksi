"""Abstract technical-service contracts (as opposed to data-access repositories).

`PasswordHasher` and `TokenService` back the auth use cases today. A future
`NotificationService` (e.g. sending a Telegram message when a partner logs an
expense) would land here too, so use cases can depend on it the same way.
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
