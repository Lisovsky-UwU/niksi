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
  carryover_override: string | null
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

/** Expected income for a month. What actually arrived is in IncomeEntry. */
export interface Income {
  id: number
  month_id: number
  user_id: number
  forecast_amount: string
}

export interface IncomeEntry {
  id: number
  month_id: number
  user_id: number
  amount: string
  description: string | null
  received_date: string
  created_by_user_id: number
}

export interface GreyZoneLimit {
  id: number
  month_id: number
  user_id: number
  amount: string
}

export interface GreyZoneEntry {
  id: number
  month_id: number
  user_id: number
  amount: string
  taken_date: string
}

export interface GreyZoneMonth {
  limits: GreyZoneLimit[]
  entries: GreyZoneEntry[]
}

export type SavingsPotKind = 'account' | 'deposit' | 'goal'
export type SavingsTransferDirection = 'in' | 'out' | 'interest'

export interface SavingsPot {
  id: number
  name: string
  kind: SavingsPotKind
  target_amount: string | null
  target_date: string | null
  is_archived: boolean
  balance: string
}

export interface SavingsTransfer {
  id: number
  pot_id: number
  direction: SavingsTransferDirection
  amount: string
  transfer_date: string
  note: string | null
  created_by_user_id: number
}

export interface Reconciliation {
  id: number
  balance_date: string
  actual_balance: string
  expected_balance: string | null
  difference: string
  note: string | null
  created_by_user_id: number
  created_at: string
}

export interface CashFlows {
  income: string
  expenses: string
  grey_zone: string
  savings_in: string
  savings_out: string
}

export interface BalanceStatus {
  last_reconciliation: Reconciliation | null
  expected_now: string | null
  flows_since: CashFlows
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

export interface GreyZoneUserSummary {
  user_id: number
  display_name: string
  limit: string
  taken: string
  remaining: string
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
  grey_zone: {
    per_user: GreyZoneUserSummary[]
    total_limit: string
    total_taken: string
  }
  balance: {
    income_actual: string
    total_spent: string
    grey_zone_taken: string
    savings_net: string
    adjustments: string
    net: string
  }
  carryover: {
    carried_over: string
    is_manual: boolean
    closing: string
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
}

export interface IncomeEntryCreateRequest {
  amount: string
  description?: string | null
  received_date: string
  user_id?: number
}

export interface SavingsPotCreateRequest {
  name: string
  kind: SavingsPotKind
  target_amount?: string | null
  target_date?: string | null
}

export interface SavingsPotUpdateRequest {
  name: string
  target_amount: string | null
  target_date: string | null
  is_archived: boolean
}

export interface SavingsTransferCreateRequest {
  direction: SavingsTransferDirection
  amount: string
  transfer_date: string
  note?: string | null
}

export interface ReconciliationCreateRequest {
  actual_balance: string
  balance_date: string
  note?: string | null
}
