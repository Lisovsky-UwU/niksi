"""FastAPI-specific dependency wiring. This is the only place that knows how to
assemble a use case out of concrete infrastructure implementations for the web
entry point. A future Telegram entry point would wire the same use cases up
itself, independently of this module.
"""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.exceptions import AuthenticationError
from app.domain.models import User
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.sqlalchemy_category_repository import SqlAlchemyCategoryRepository
from app.infrastructure.repositories.sqlalchemy_expense_repository import SqlAlchemyExpenseRepository
from app.infrastructure.repositories.sqlalchemy_grey_zone_repository import SqlAlchemyGreyZoneRepository
from app.infrastructure.repositories.sqlalchemy_income_repository import SqlAlchemyIncomeRepository
from app.infrastructure.repositories.sqlalchemy_ledger_repository import SqlAlchemyLedgerRepository
from app.infrastructure.repositories.sqlalchemy_month_repository import SqlAlchemyMonthRepository
from app.infrastructure.repositories.sqlalchemy_reconciliation_repository import SqlAlchemyReconciliationRepository
from app.infrastructure.repositories.sqlalchemy_savings_repository import SqlAlchemySavingsRepository
from app.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.infrastructure.security import Argon2PasswordHasher, JwtTokenService
from app.interfaces.repositories import (
    CategoryRepository,
    ExpenseRepository,
    GreyZoneRepository,
    IncomeRepository,
    LedgerRepository,
    MonthRepository,
    ReconciliationRepository,
    SavingsRepository,
    UserRepository,
)
from app.interfaces.services import PasswordHasher, TokenService
from app.use_cases.auth import GetCurrentUserUseCase, LoginUseCase
from app.use_cases.categories import (
    CopyCategoriesFromPreviousMonthUseCase,
    CreateCategoryUseCase,
    DeleteCategoryUseCase,
    ListCategoriesUseCase,
    UpdateCategoryUseCase,
)
from app.use_cases.expenses import (
    AddExpenseUseCase,
    DeleteExpenseUseCase,
    ListExpensesUseCase,
    UpdateExpenseUseCase,
)
from app.use_cases.grey_zone import (
    DeleteGreyZoneEntryUseCase,
    GetGreyZoneForMonthUseCase,
    SetMyGreyZoneLimitUseCase,
    TakeFromGreyZoneUseCase,
)
from app.use_cases.income import (
    AddIncomeEntryUseCase,
    DeleteIncomeEntryUseCase,
    GetIncomeForMonthUseCase,
    ListIncomeEntriesUseCase,
    SetMyIncomeUseCase,
)
from app.use_cases.months import (
    CopyPlansFromPreviousMonthUseCase,
    CreateMonthUseCase,
    GetMonthUseCase,
    ListMonthsUseCase,
    SetCarryoverUseCase,
)
from app.use_cases.reconciliation import (
    CreateReconciliationUseCase,
    DeleteReconciliationUseCase,
    GetBalanceStatusUseCase,
    ListReconciliationsUseCase,
)
from app.use_cases.savings import (
    AddSavingsTransferUseCase,
    CreateSavingsPotUseCase,
    DeleteSavingsPotUseCase,
    DeleteSavingsTransferUseCase,
    ListSavingsPotsUseCase,
    ListSavingsTransfersUseCase,
    UpdateSavingsPotUseCase,
)
from app.use_cases.summary import GetMonthSummaryUseCase
from app.use_cases.users import ListUsersUseCase

COOKIE_NAME = "access_token"

_password_hasher = Argon2PasswordHasher()
_token_service = JwtTokenService(settings.secret_key, settings.jwt_algorithm, settings.jwt_expires_days)


# ---- repositories ----


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return SqlAlchemyUserRepository(db)


def get_month_repository(db: Session = Depends(get_db)) -> MonthRepository:
    return SqlAlchemyMonthRepository(db)


def get_category_repository(db: Session = Depends(get_db)) -> CategoryRepository:
    return SqlAlchemyCategoryRepository(db)


def get_expense_repository(db: Session = Depends(get_db)) -> ExpenseRepository:
    return SqlAlchemyExpenseRepository(db)


def get_income_repository(db: Session = Depends(get_db)) -> IncomeRepository:
    return SqlAlchemyIncomeRepository(db)


def get_grey_zone_repository(db: Session = Depends(get_db)) -> GreyZoneRepository:
    return SqlAlchemyGreyZoneRepository(db)


def get_savings_repository(db: Session = Depends(get_db)) -> SavingsRepository:
    return SqlAlchemySavingsRepository(db)


def get_reconciliation_repository(db: Session = Depends(get_db)) -> ReconciliationRepository:
    return SqlAlchemyReconciliationRepository(db)


def get_ledger_repository(db: Session = Depends(get_db)) -> LedgerRepository:
    return SqlAlchemyLedgerRepository(db)


# ---- services ----


def get_password_hasher() -> PasswordHasher:
    return _password_hasher


def get_token_service() -> TokenService:
    return _token_service


# ---- use cases ----


def get_login_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    token_service: TokenService = Depends(get_token_service),
) -> LoginUseCase:
    return LoginUseCase(user_repo, password_hasher, token_service)


def get_current_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
    token_service: TokenService = Depends(get_token_service),
) -> GetCurrentUserUseCase:
    return GetCurrentUserUseCase(user_repo, token_service)


def get_list_months_use_case(month_repo: MonthRepository = Depends(get_month_repository)) -> ListMonthsUseCase:
    return ListMonthsUseCase(month_repo)


def get_get_month_use_case(month_repo: MonthRepository = Depends(get_month_repository)) -> GetMonthUseCase:
    return GetMonthUseCase(month_repo)


def get_copy_categories_use_case(
    month_repo: MonthRepository = Depends(get_month_repository),
    category_repo: CategoryRepository = Depends(get_category_repository),
) -> CopyCategoriesFromPreviousMonthUseCase:
    return CopyCategoriesFromPreviousMonthUseCase(month_repo, category_repo)


def get_copy_plans_use_case(
    month_repo: MonthRepository = Depends(get_month_repository),
    income_repo: IncomeRepository = Depends(get_income_repository),
    grey_zone_repo: GreyZoneRepository = Depends(get_grey_zone_repository),
) -> CopyPlansFromPreviousMonthUseCase:
    return CopyPlansFromPreviousMonthUseCase(month_repo, income_repo, grey_zone_repo)


def get_create_month_use_case(
    month_repo: MonthRepository = Depends(get_month_repository),
    copy_use_case: CopyCategoriesFromPreviousMonthUseCase = Depends(get_copy_categories_use_case),
    copy_plans_use_case: CopyPlansFromPreviousMonthUseCase = Depends(get_copy_plans_use_case),
) -> CreateMonthUseCase:
    return CreateMonthUseCase(month_repo, copy_use_case, copy_plans_use_case)


def get_set_carryover_use_case(month_repo: MonthRepository = Depends(get_month_repository)) -> SetCarryoverUseCase:
    return SetCarryoverUseCase(month_repo)


def get_list_users_use_case(user_repo: UserRepository = Depends(get_user_repository)) -> ListUsersUseCase:
    return ListUsersUseCase(user_repo)


def get_list_categories_use_case(
    category_repo: CategoryRepository = Depends(get_category_repository),
) -> ListCategoriesUseCase:
    return ListCategoriesUseCase(category_repo)


def get_create_category_use_case(
    category_repo: CategoryRepository = Depends(get_category_repository),
    month_repo: MonthRepository = Depends(get_month_repository),
) -> CreateCategoryUseCase:
    return CreateCategoryUseCase(category_repo, month_repo)


def get_update_category_use_case(
    category_repo: CategoryRepository = Depends(get_category_repository),
) -> UpdateCategoryUseCase:
    return UpdateCategoryUseCase(category_repo)


def get_delete_category_use_case(
    category_repo: CategoryRepository = Depends(get_category_repository),
) -> DeleteCategoryUseCase:
    return DeleteCategoryUseCase(category_repo)


def get_list_expenses_use_case(
    expense_repo: ExpenseRepository = Depends(get_expense_repository),
) -> ListExpensesUseCase:
    return ListExpensesUseCase(expense_repo)


def get_add_expense_use_case(
    expense_repo: ExpenseRepository = Depends(get_expense_repository),
    category_repo: CategoryRepository = Depends(get_category_repository),
) -> AddExpenseUseCase:
    return AddExpenseUseCase(expense_repo, category_repo)


def get_update_expense_use_case(
    expense_repo: ExpenseRepository = Depends(get_expense_repository),
) -> UpdateExpenseUseCase:
    return UpdateExpenseUseCase(expense_repo)


def get_delete_expense_use_case(
    expense_repo: ExpenseRepository = Depends(get_expense_repository),
) -> DeleteExpenseUseCase:
    return DeleteExpenseUseCase(expense_repo)


def get_income_for_month_use_case(
    income_repo: IncomeRepository = Depends(get_income_repository),
) -> GetIncomeForMonthUseCase:
    return GetIncomeForMonthUseCase(income_repo)


def get_set_my_income_use_case(
    income_repo: IncomeRepository = Depends(get_income_repository),
    month_repo: MonthRepository = Depends(get_month_repository),
) -> SetMyIncomeUseCase:
    return SetMyIncomeUseCase(income_repo, month_repo)


def get_list_income_entries_use_case(
    income_repo: IncomeRepository = Depends(get_income_repository),
) -> ListIncomeEntriesUseCase:
    return ListIncomeEntriesUseCase(income_repo)


def get_add_income_entry_use_case(
    income_repo: IncomeRepository = Depends(get_income_repository),
    month_repo: MonthRepository = Depends(get_month_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> AddIncomeEntryUseCase:
    return AddIncomeEntryUseCase(income_repo, month_repo, user_repo)


def get_delete_income_entry_use_case(
    income_repo: IncomeRepository = Depends(get_income_repository),
) -> DeleteIncomeEntryUseCase:
    return DeleteIncomeEntryUseCase(income_repo)


def get_grey_zone_for_month_use_case(
    grey_zone_repo: GreyZoneRepository = Depends(get_grey_zone_repository),
) -> GetGreyZoneForMonthUseCase:
    return GetGreyZoneForMonthUseCase(grey_zone_repo)


def get_set_my_grey_zone_limit_use_case(
    grey_zone_repo: GreyZoneRepository = Depends(get_grey_zone_repository),
    month_repo: MonthRepository = Depends(get_month_repository),
) -> SetMyGreyZoneLimitUseCase:
    return SetMyGreyZoneLimitUseCase(grey_zone_repo, month_repo)


def get_take_from_grey_zone_use_case(
    grey_zone_repo: GreyZoneRepository = Depends(get_grey_zone_repository),
    month_repo: MonthRepository = Depends(get_month_repository),
) -> TakeFromGreyZoneUseCase:
    return TakeFromGreyZoneUseCase(grey_zone_repo, month_repo)


def get_delete_grey_zone_entry_use_case(
    grey_zone_repo: GreyZoneRepository = Depends(get_grey_zone_repository),
) -> DeleteGreyZoneEntryUseCase:
    return DeleteGreyZoneEntryUseCase(grey_zone_repo)


def get_list_savings_pots_use_case(
    savings_repo: SavingsRepository = Depends(get_savings_repository),
) -> ListSavingsPotsUseCase:
    return ListSavingsPotsUseCase(savings_repo)


def get_create_savings_pot_use_case(
    savings_repo: SavingsRepository = Depends(get_savings_repository),
) -> CreateSavingsPotUseCase:
    return CreateSavingsPotUseCase(savings_repo)


def get_update_savings_pot_use_case(
    savings_repo: SavingsRepository = Depends(get_savings_repository),
) -> UpdateSavingsPotUseCase:
    return UpdateSavingsPotUseCase(savings_repo)


def get_delete_savings_pot_use_case(
    savings_repo: SavingsRepository = Depends(get_savings_repository),
) -> DeleteSavingsPotUseCase:
    return DeleteSavingsPotUseCase(savings_repo)


def get_list_savings_transfers_use_case(
    savings_repo: SavingsRepository = Depends(get_savings_repository),
) -> ListSavingsTransfersUseCase:
    return ListSavingsTransfersUseCase(savings_repo)


def get_add_savings_transfer_use_case(
    savings_repo: SavingsRepository = Depends(get_savings_repository),
) -> AddSavingsTransferUseCase:
    return AddSavingsTransferUseCase(savings_repo)


def get_delete_savings_transfer_use_case(
    savings_repo: SavingsRepository = Depends(get_savings_repository),
) -> DeleteSavingsTransferUseCase:
    return DeleteSavingsTransferUseCase(savings_repo)


def get_balance_status_use_case(
    reconciliation_repo: ReconciliationRepository = Depends(get_reconciliation_repository),
    ledger_repo: LedgerRepository = Depends(get_ledger_repository),
) -> GetBalanceStatusUseCase:
    return GetBalanceStatusUseCase(reconciliation_repo, ledger_repo)


def get_list_reconciliations_use_case(
    reconciliation_repo: ReconciliationRepository = Depends(get_reconciliation_repository),
) -> ListReconciliationsUseCase:
    return ListReconciliationsUseCase(reconciliation_repo)


def get_create_reconciliation_use_case(
    reconciliation_repo: ReconciliationRepository = Depends(get_reconciliation_repository),
    ledger_repo: LedgerRepository = Depends(get_ledger_repository),
) -> CreateReconciliationUseCase:
    return CreateReconciliationUseCase(reconciliation_repo, ledger_repo)


def get_delete_reconciliation_use_case(
    reconciliation_repo: ReconciliationRepository = Depends(get_reconciliation_repository),
) -> DeleteReconciliationUseCase:
    return DeleteReconciliationUseCase(reconciliation_repo)


def get_month_summary_use_case(
    month_repo: MonthRepository = Depends(get_month_repository),
    category_repo: CategoryRepository = Depends(get_category_repository),
    expense_repo: ExpenseRepository = Depends(get_expense_repository),
    income_repo: IncomeRepository = Depends(get_income_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    grey_zone_repo: GreyZoneRepository = Depends(get_grey_zone_repository),
    savings_repo: SavingsRepository = Depends(get_savings_repository),
    reconciliation_repo: ReconciliationRepository = Depends(get_reconciliation_repository),
) -> GetMonthSummaryUseCase:
    return GetMonthSummaryUseCase(
        month_repo,
        category_repo,
        expense_repo,
        income_repo,
        user_repo,
        grey_zone_repo,
        savings_repo,
        reconciliation_repo,
    )


# ---- current user (auth guard) ----


def get_current_user(
    request: Request,
    use_case: GetCurrentUserUseCase = Depends(get_current_user_use_case),
) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise AuthenticationError("Not authenticated")
    return use_case.execute(token)
