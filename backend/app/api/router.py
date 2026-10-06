from fastapi import APIRouter

from app.api.routes import (
    auth,
    balance,
    categories,
    expenses,
    grey_zone,
    income,
    loans,
    months,
    savings,
    summary,
    users,
)

router = APIRouter(prefix="/api")
router.include_router(auth.router)
router.include_router(users.router)
# Routers with a literal path suffix under /months/{id}/... must be registered before
# months.router: its GET /months/{year}/{month} has two plain path variables, which would
# otherwise greedily match paths like /months/5/categories or /months/5/summary first.
router.include_router(categories.router)
router.include_router(expenses.router)
router.include_router(income.router)
router.include_router(income.entries_router)
router.include_router(grey_zone.router)
router.include_router(grey_zone.entries_router)
router.include_router(summary.router)
router.include_router(months.router)
router.include_router(savings.router)
router.include_router(loans.router)
router.include_router(balance.router)
