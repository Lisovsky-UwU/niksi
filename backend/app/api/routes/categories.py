from fastapi import APIRouter, Depends, status

from app.api.deps import (
    get_copy_categories_use_case,
    get_create_category_use_case,
    get_current_user,
    get_delete_category_use_case,
    get_list_categories_use_case,
    get_update_category_use_case,
)
from app.api.schemas import CategoryCreateRequest, CategoryUpdateRequest
from app.domain.models import Category, User
from app.use_cases.categories import (
    CopyCategoriesFromPreviousMonthUseCase,
    CreateCategoryUseCase,
    DeleteCategoryUseCase,
    ListCategoriesUseCase,
    UpdateCategoryUseCase,
)

router = APIRouter(tags=["categories"])


@router.get("/months/{month_id}/categories", response_model=list[Category])
def list_categories(
    month_id: int,
    use_case: ListCategoriesUseCase = Depends(get_list_categories_use_case),
    _current_user: User = Depends(get_current_user),
) -> list[Category]:
    return use_case.execute(month_id)


@router.post("/months/{month_id}/categories", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(
    month_id: int,
    payload: CategoryCreateRequest,
    use_case: CreateCategoryUseCase = Depends(get_create_category_use_case),
    _current_user: User = Depends(get_current_user),
) -> Category:
    return use_case.execute(month_id, payload.name, payload.limit_amount, payload.color)


@router.put("/categories/{category_id}", response_model=Category)
def update_category(
    category_id: int,
    payload: CategoryUpdateRequest,
    use_case: UpdateCategoryUseCase = Depends(get_update_category_use_case),
    _current_user: User = Depends(get_current_user),
) -> Category:
    clear_color = payload.color == "auto"
    color = None if clear_color else payload.color
    return use_case.execute(
        category_id, payload.name, payload.limit_amount, payload.position, color, clear_color  # type: ignore[arg-type]
    )


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    use_case: DeleteCategoryUseCase = Depends(get_delete_category_use_case),
    _current_user: User = Depends(get_current_user),
) -> None:
    use_case.execute(category_id)


@router.post("/months/{month_id}/categories/copy-from-previous", response_model=list[Category])
def copy_categories_from_previous(
    month_id: int,
    use_case: CopyCategoriesFromPreviousMonthUseCase = Depends(get_copy_categories_use_case),
    _current_user: User = Depends(get_current_user),
) -> list[Category]:
    return use_case.execute(month_id)
