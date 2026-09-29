from fastapi import APIRouter, Depends, Response

from app.api.deps import COOKIE_NAME, get_current_user, get_login_use_case
from app.api.schemas import LoginRequest
from app.core.config import settings
from app.domain.models import User
from app.use_cases.auth import LoginUseCase

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=User)
def login(payload: LoginRequest, response: Response, use_case: LoginUseCase = Depends(get_login_use_case)) -> User:
    user, token = use_case.execute(payload.email, payload.password)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=60 * 60 * 24 * settings.jwt_expires_days,
        path="/",
    )
    return user


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me", response_model=User)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
