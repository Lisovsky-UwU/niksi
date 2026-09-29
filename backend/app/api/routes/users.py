from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import (
    get_avatar_use_case,
    get_create_telegram_link_code_use_case,
    get_change_my_password_use_case,
    get_current_user,
    get_list_users_use_case,
    get_set_my_avatar_use_case,
    get_unlink_telegram_use_case,
    get_update_my_profile_use_case,
)
from app.api.schemas import PasswordChangeRequest, ProfileUpdateRequest
from app.core.config import settings
from app.domain.models import Avatar, TelegramLinkCode, User
from app.use_cases.users import (
    ChangeMyPasswordUseCase,
    GetAvatarUseCase,
    ListUsersUseCase,
    SetMyAvatarUseCase,
    UpdateMyProfileUseCase,
)
from app.use_cases.telegram import CreateTelegramLinkCodeUseCase, UnlinkTelegramUseCase

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[User])
def list_users(
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
    _current_user: User = Depends(get_current_user),
) -> list[User]:
    return use_case.execute()


@router.put("/me", response_model=User)
def update_my_profile(
    payload: ProfileUpdateRequest,
    use_case: UpdateMyProfileUseCase = Depends(get_update_my_profile_use_case),
    current_user: User = Depends(get_current_user),
) -> User:
    return use_case.execute(current_user.id, payload.display_name)


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    payload: PasswordChangeRequest,
    use_case: ChangeMyPasswordUseCase = Depends(get_change_my_password_use_case),
    current_user: User = Depends(get_current_user),
) -> None:
    use_case.execute(current_user.id, payload.current_password, payload.new_password)


# The image is sent as the raw request body (Content-Type: image/webp etc.), already
# cropped and shrunk in the browser, so no multipart parsing is needed.
@router.put("/me/avatar", response_model=User)
async def set_my_avatar(
    request: Request,
    use_case: SetMyAvatarUseCase = Depends(get_set_my_avatar_use_case),
    current_user: User = Depends(get_current_user),
) -> User:
    content_type = request.headers.get("content-type", "").split(";")[0].strip()
    data = await request.body()
    return use_case.execute(current_user.id, Avatar(content_type=content_type, data=data))


@router.delete("/me/avatar", response_model=User)
def remove_my_avatar(
    use_case: SetMyAvatarUseCase = Depends(get_set_my_avatar_use_case),
    current_user: User = Depends(get_current_user),
) -> User:
    return use_case.execute(current_user.id, None)


@router.get("/{user_id}/avatar")
def get_avatar(
    user_id: int,
    use_case: GetAvatarUseCase = Depends(get_avatar_use_case),
    _current_user: User = Depends(get_current_user),
) -> Response:
    avatar = use_case.execute(user_id)
    # URLs carry ?v=<avatar_version>, so a given URL never changes content.
    return Response(
        content=avatar.data,
        media_type=avatar.content_type,
        headers={"Cache-Control": "private, max-age=31536000, immutable"},
    )


@router.post("/me/telegram-code", response_model=TelegramLinkCode)
def create_telegram_link_code(
    use_case: CreateTelegramLinkCodeUseCase = Depends(get_create_telegram_link_code_use_case),
    current_user: User = Depends(get_current_user),
) -> TelegramLinkCode:
    code = use_case.execute(current_user.id, datetime.now(UTC))
    return code.model_copy(update={"bot_username": settings.telegram_bot_username})


@router.delete("/me/telegram", response_model=User)
def unlink_telegram(
    use_case: UnlinkTelegramUseCase = Depends(get_unlink_telegram_use_case),
    current_user: User = Depends(get_current_user),
) -> User:
    return use_case.execute(current_user.id)
