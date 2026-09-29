from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_list_users_use_case
from app.domain.models import User
from app.use_cases.users import ListUsersUseCase

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[User])
def list_users(
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
    _current_user: User = Depends(get_current_user),
) -> list[User]:
    return use_case.execute()
