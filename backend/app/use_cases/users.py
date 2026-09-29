from app.domain.exceptions import NotFoundError, ValidationError
from app.domain.models import Avatar, User
from app.interfaces.repositories import UserRepository
from app.interfaces.services import PasswordHasher

# The browser crops and shrinks the picture to a small square before upload,
# so anything much larger than this is not an avatar.
MAX_AVATAR_BYTES = 512 * 1024
AVATAR_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ListUsersUseCase:
    """Both partners, so the UI can show each person even before they entered anything."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self) -> list[User]:
        return self._user_repo.list_all()


class UpdateMyProfileUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, user_id: int, display_name: str) -> User:
        name = display_name.strip()
        if not name:
            raise ValidationError("The name cannot be empty")
        return self._user_repo.update_display_name(user_id, name)


class ChangeMyPasswordUseCase:
    def __init__(self, user_repo: UserRepository, password_hasher: PasswordHasher) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher

    def execute(self, user_id: int, current_password: str, new_password: str) -> None:
        credentials = self._user_repo.get_credentials_by_id(user_id)
        if credentials is None:
            raise NotFoundError(f"User {user_id} not found")
        if not self._password_hasher.verify(current_password, credentials.password_hash):
            raise ValidationError("The current password is wrong")
        self._user_repo.update_password_hash(user_id, self._password_hasher.hash(new_password))


class SetMyAvatarUseCase:
    """A None avatar removes the picture and brings back the initial letter."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, user_id: int, avatar: Avatar | None) -> User:
        if avatar is not None:
            if avatar.content_type not in AVATAR_CONTENT_TYPES:
                raise ValidationError("The avatar must be a JPEG, PNG or WebP image")
            if not avatar.data or len(avatar.data) > MAX_AVATAR_BYTES:
                raise ValidationError("The avatar image is empty or too large")
        return self._user_repo.set_avatar(user_id, avatar)


class GetAvatarUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, user_id: int) -> Avatar:
        avatar = self._user_repo.get_avatar(user_id)
        if avatar is None:
            raise NotFoundError(f"User {user_id} has no avatar")
        return avatar
