// Mirrors the backend's Pydantic domain models (app/domain/models.py) and input
// schemas (app/api/schemas.py). Monetary amounts travel over JSON as decimal
// strings (e.g. "1500.50"), matching how FastAPI serializes Python Decimal.

export interface User {
  id: number
  email: string
  display_name: string
}

export interface Month {
  id: number
  year: number
  month: number
}

export interface Category {
  id: number
  month_id: number
  name: string
  limit_amount: string
  position: number
}

export interface Expense {
  id: number
  category_id: number
  amount: string
  description: string | null
  expense_date: string
  created_by_user_id: number
}

export interface Income {
  id: number
  month_id: number
  user_id: number
  forecast_amount: string
  actual_amount: string
}

export interface CategorySummary {
  id: number
  name: string
  limit_amount: string
  spent: string
  remaining: string
  percent_used: number
}

export interface UserIncomeSummary {
  user_id: number
  display_name: string
  forecast: string
  actual: string
}

export interface MonthSummary {
  month: Month
  categories: CategorySummary[]
  totals: {
    total_limit: string
    total_spent: string
  }
  income: {
    per_user: UserIncomeSummary[]
    household_forecast: string
    household_actual: string
  }
  balance: {
    income_actual: string
    total_spent: string
    net: string
  }
}

export interface LoginRequest {
  email: string
  password: string
}

export interface MonthCreateRequest {
  year: number
  month: number
  copy_categories_from_previous: boolean
}

export interface CategoryCreateRequest {
  name: string
  limit_amount: string
}

export interface CategoryUpdateRequest {
  name?: string
  limit_amount?: string
  position?: number
}

export interface ExpenseCreateRequest {
  category_id: number
  amount: string
  description?: string | null
  expense_date: string
}

export interface ExpenseUpdateRequest {
  amount?: string
  description?: string | null
  expense_date?: string
}

export interface IncomeSetRequest {
  forecast_amount: string
  actual_amount: string
}
