from app.domain.models import User
from app.interfaces.repositories import UserRepository


class ListUsersUseCase:
    """Both partners, so the UI can show each person even before they entered anything."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self) -> list[User]:
        return self._user_repo.list_all()
