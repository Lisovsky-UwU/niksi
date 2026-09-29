from fastapi import APIRouter, Depends, status

from app.api.deps import (
    get_add_savings_transfer_use_case,
    get_create_savings_pot_use_case,
    get_current_user,
    get_delete_savings_pot_use_case,
    get_delete_savings_transfer_use_case,
    get_list_savings_pots_use_case,
    get_list_savings_transfers_use_case,
    get_update_savings_pot_use_case,
)
from app.api.schemas import SavingsPotCreateRequest, SavingsPotUpdateRequest, SavingsTransferCreateRequest
from app.domain.models import SavingsPot, SavingsTransfer, User
from app.use_cases.savings import (
    AddSavingsTransferUseCase,
    CreateSavingsPotUseCase,
    DeleteSavingsPotUseCase,
    DeleteSavingsTransferUseCase,
    ListSavingsPotsUseCase,
    ListSavingsTransfersUseCase,
    UpdateSavingsPotUseCase,
)

router = APIRouter(prefix="/savings", tags=["savings"])


@router.get("/pots", response_model=list[SavingsPot])
def list_pots(
    include_archived: bool = False,
    use_case: ListSavingsPotsUseCase = Depends(get_list_savings_pots_use_case),
    _current_user: User = Depends(get_current_user),
) -> list[SavingsPot]:
    return use_case.execute(include_archived)


@router.post("/pots", response_model=SavingsPot, status_code=status.HTTP_201_CREATED)
def create_pot(
    payload: SavingsPotCreateRequest,
    use_case: CreateSavingsPotUseCase = Depends(get_create_savings_pot_use_case),
    _current_user: User = Depends(get_current_user),
) -> SavingsPot:
    return use_case.execute(payload.name, payload.kind, payload.target_amount, payload.target_date)


@router.put("/pots/{pot_id}", response_model=SavingsPot)
def update_pot(
    pot_id: int,
    payload: SavingsPotUpdateRequest,
    use_case: UpdateSavingsPotUseCase = Depends(get_update_savings_pot_use_case),
    _current_user: User = Depends(get_current_user),
) -> SavingsPot:
    return use_case.execute(pot_id, payload.name, payload.target_amount, payload.target_date, payload.is_archived)


@router.delete("/pots/{pot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pot(
    pot_id: int,
    use_case: DeleteSavingsPotUseCase = Depends(get_delete_savings_pot_use_case),
    _current_user: User = Depends(get_current_user),
) -> None:
    use_case.execute(pot_id)


@router.get("/pots/{pot_id}/transfers", response_model=list[SavingsTransfer])
def list_transfers(
    pot_id: int,
    use_case: ListSavingsTransfersUseCase = Depends(get_list_savings_transfers_use_case),
    _current_user: User = Depends(get_current_user),
) -> list[SavingsTransfer]:
    return use_case.execute(pot_id)


@router.post("/pots/{pot_id}/transfers", response_model=SavingsTransfer, status_code=status.HTTP_201_CREATED)
def add_transfer(
    pot_id: int,
    payload: SavingsTransferCreateRequest,
    use_case: AddSavingsTransferUseCase = Depends(get_add_savings_transfer_use_case),
    current_user: User = Depends(get_current_user),
) -> SavingsTransfer:
    return use_case.execute(
        pot_id, payload.direction, payload.amount, payload.transfer_date, payload.note, current_user.id
    )


@router.delete("/transfers/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transfer(
    transfer_id: int,
    use_case: DeleteSavingsTransferUseCase = Depends(get_delete_savings_transfer_use_case),
    _current_user: User = Depends(get_current_user),
) -> None:
    use_case.execute(transfer_id)
