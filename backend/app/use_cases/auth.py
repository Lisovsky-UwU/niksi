from app.domain.exceptions import AuthenticationError
from app.domain.models import User
from app.interfaces.repositories import UserRepository
from app.interfaces.services import PasswordHasher, TokenService


class LoginUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._token_service = token_service

    def execute(self, email: str, password: str) -> tuple[User, str]:
        credentials = self._user_repo.get_credentials_by_email(email)
        if credentials is None or not self._password_hasher.verify(password, credentials.password_hash):
            raise AuthenticationError("Invalid email or password")
        token = self._token_service.create_token(credentials.id)
        user = self._user_repo.get_by_id(credentials.id)
        assert user is not None
        return user, token


class GetCurrentUserUseCase:
    def __init__(self, user_repo: UserRepository, token_service: TokenService) -> None:
        self._user_repo = user_repo
        self._token_service = token_service

    def execute(self, token: str) -> User:
        user_id = self._token_service.decode_token(token)
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("User for token no longer exists")
        return user
