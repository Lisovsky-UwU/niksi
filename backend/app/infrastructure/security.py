from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.domain.exceptions import AuthenticationError
from app.interfaces.services import PasswordHasher, TokenService


class Argon2PasswordHasher(PasswordHasher):
    def __init__(self) -> None:
        self._hasher = Argon2Hasher()

    def hash(self, plain_password: str) -> str:
        return self._hasher.hash(plain_password)

    def verify(self, plain_password: str, password_hash: str) -> bool:
        try:
            return self._hasher.verify(password_hash, plain_password)
        except (VerifyMismatchError, InvalidHashError):
            return False


class JwtTokenService(TokenService):
    def __init__(self, secret_key: str, algorithm: str = "HS256", expires_days: int = 30) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expires_days = expires_days

    def create_token(self, user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(days=self._expires_days),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_token(self, token: str) -> int:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            return int(payload["sub"])
        except (jwt.PyJWTError, KeyError, ValueError, TypeError) as exc:
            raise AuthenticationError("Invalid or expired token") from exc
