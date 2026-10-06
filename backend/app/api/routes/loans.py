from fastapi import APIRouter, Depends, status

from app.api.deps import (
    get_add_loan_payment_use_case,
    get_create_loan_use_case,
    get_current_user,
    get_delete_loan_payment_use_case,
    get_delete_loan_use_case,
    get_list_loan_payments_use_case,
    get_list_loans_use_case,
    get_update_loan_use_case,
)
from app.api.schemas import LoanCreateRequest, LoanPaymentCreateRequest, LoanUpdateRequest
from app.domain.models import Loan, LoanPayment, User
from app.use_cases.loans import (
    AddLoanPaymentUseCase,
    CreateLoanUseCase,
    DeleteLoanPaymentUseCase,
    DeleteLoanUseCase,
    ListLoanPaymentsUseCase,
    ListLoansUseCase,
    UpdateLoanUseCase,
)

router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("", response_model=list[Loan])
def list_loans(
    use_case: ListLoansUseCase = Depends(get_list_loans_use_case),
    _current_user: User = Depends(get_current_user),
) -> list[Loan]:
    return use_case.execute()


@router.post("", response_model=Loan, status_code=status.HTTP_201_CREATED)
def create_loan(
    payload: LoanCreateRequest,
    use_case: CreateLoanUseCase = Depends(get_create_loan_use_case),
    _current_user: User = Depends(get_current_user),
) -> Loan:
    return use_case.execute(
        payload.name,
        payload.principal,
        payload.start_date,
        payload.rate_percent,
        payload.monthly_payment,
        payload.payment_day,
    )


@router.put("/{loan_id}", response_model=Loan)
def update_loan(
    loan_id: int,
    payload: LoanUpdateRequest,
    use_case: UpdateLoanUseCase = Depends(get_update_loan_use_case),
    _current_user: User = Depends(get_current_user),
) -> Loan:
    return use_case.execute(
        loan_id,
        payload.name,
        payload.principal,
        payload.start_date,
        payload.rate_percent,
        payload.monthly_payment,
        payload.payment_day,
        payload.is_closed,
    )


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(
    loan_id: int,
    use_case: DeleteLoanUseCase = Depends(get_delete_loan_use_case),
    _current_user: User = Depends(get_current_user),
) -> None:
    use_case.execute(loan_id)


@router.get("/{loan_id}/payments", response_model=list[LoanPayment])
def list_payments(
    loan_id: int,
    use_case: ListLoanPaymentsUseCase = Depends(get_list_loan_payments_use_case),
    _current_user: User = Depends(get_current_user),
) -> list[LoanPayment]:
    return use_case.execute(loan_id)


@router.post("/{loan_id}/payments", response_model=LoanPayment, status_code=status.HTTP_201_CREATED)
def add_payment(
    loan_id: int,
    payload: LoanPaymentCreateRequest,
    use_case: AddLoanPaymentUseCase = Depends(get_add_loan_payment_use_case),
    current_user: User = Depends(get_current_user),
) -> LoanPayment:
    return use_case.execute(
        loan_id,
        payload.kind,
        payload.amount,
        payload.new_balance,
        payload.payment_date,
        payload.note,
        current_user.id,
    )


@router.delete("/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: int,
    use_case: DeleteLoanPaymentUseCase = Depends(get_delete_loan_payment_use_case),
    _current_user: User = Depends(get_current_user),
) -> None:
    use_case.execute(payment_id)
