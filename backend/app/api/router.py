from fastapi import APIRouter

from app.api.routes import auth, categories, expenses, income, months, summary

router = APIRouter(prefix="/api")
router.include_router(auth.router)
# Routers with a literal path suffix under /months/{id}/... must be registered before
# months.router: its GET /months/{year}/{month} has two plain path variables, which would
# otherwise greedily match paths like /months/5/categories or /months/5/summary first.
router.include_router(categories.router)
router.include_router(expenses.router)
router.include_router(income.router)
router.include_router(summary.router)
router.include_router(months.router)
