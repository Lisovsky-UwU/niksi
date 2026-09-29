from datetime import date

from fastapi import APIRouter, Depends, status

from app.api.deps import (
    get_balance_status_use_case,
    get_create_reconciliation_use_case,
    get_current_user,
    get_delete_reconciliation_use_case,
    get_list_reconciliations_use_case,
)
from app.api.schemas import ReconciliationCreateRequest
from app.domain.models import BalanceStatus, Reconciliation, User
from app.use_cases.reconciliation import (
    CreateReconciliationUseCase,
    DeleteReconciliationUseCase,
    GetBalanceStatusUseCase,
    ListReconciliationsUseCase,
)

router = APIRouter(tags=["balance"])


@router.get("/balance", response_model=BalanceStatus)
def get_balance(
    use_case: GetBalanceStatusUseCase = Depends(get_balance_status_use_case),
    _current_user: User = Depends(get_current_user),
) -> BalanceStatus:
    return use_case.execute(date.today())


@router.get("/reconciliations", response_model=list[Reconciliation])
def list_reconciliations(
    use_case: ListReconciliationsUseCase = Depends(get_list_reconciliations_use_case),
    _current_user: User = Depends(get_current_user),
) -> list[Reconciliation]:
    return use_case.execute()


@router.post("/reconciliations", response_model=Reconciliation, status_code=status.HTTP_201_CREATED)
def create_reconciliation(
    payload: ReconciliationCreateRequest,
    use_case: CreateReconciliationUseCase = Depends(get_create_reconciliation_use_case),
    current_user: User = Depends(get_current_user),
) -> Reconciliation:
    return use_case.execute(payload.balance_date, payload.actual_balance, payload.note, current_user.id)


@router.delete("/reconciliations/{reconciliation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reconciliation(
    reconciliation_id: int,
    use_case: DeleteReconciliationUseCase = Depends(get_delete_reconciliation_use_case),
    _current_user: User = Depends(get_current_user),
) -> None:
    use_case.execute(reconciliation_id)
