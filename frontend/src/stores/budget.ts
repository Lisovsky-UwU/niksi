import { defineStore } from 'pinia'
import {
  copyCategoriesFromPrevious as apiCopyCategoriesFromPrevious,
  createCategory as apiCreateCategory,
  deleteCategory as apiDeleteCategory,
  listCategories,
  updateCategory as apiUpdateCategory,
} from '../api/categories'
import {
  addExpense as apiAddExpense,
  deleteExpense as apiDeleteExpense,
  listExpenses,
} from '../api/expenses'
import {
  deleteGreyZoneEntry as apiDeleteGreyZoneEntry,
  getGreyZone,
  setMyGreyZoneLimit as apiSetMyGreyZoneLimit,
  takeFromGreyZone as apiTakeFromGreyZone,
} from '../api/greyZone'
import {
  addIncomeEntry as apiAddIncomeEntry,
  deleteIncomeEntry as apiDeleteIncomeEntry,
  getIncomeForMonth,
  listIncomeEntries,
  setMyIncome as apiSetMyIncome,
} from '../api/income'
import { getMonthSummary, setCarryover as apiSetCarryover } from '../api/months'
import { listUsers } from '../api/users'
import type {
  Category,
  CategoryCreateRequest,
  CategoryUpdateRequest,
  Expense,
  ExpenseCreateRequest,
  GreyZoneMonth,
  Income,
  IncomeEntry,
  IncomeEntryCreateRequest,
  Month,
  MonthSummary,
  User,
} from '../types/models'

export const useBudgetStore = defineStore('budget', {
  state: () => ({
    monthId: null as number | null,
    month: null as Month | null,
    summary: null as MonthSummary | null,
    categories: [] as Category[],
    expenses: [] as Expense[],
    income: [] as Income[],
    incomeEntries: [] as IncomeEntry[],
    greyZone: { limits: [], entries: [] } as GreyZoneMonth,
    users: [] as User[],
    loading: false,
  }),
  getters: {
    userName: (state) => (userId: number) => state.users.find((u) => u.id === userId)?.display_name ?? '',
  },
  actions: {
    async loadForMonth(monthId: number) {
      this.loading = true
      this.monthId = monthId
      try {
        const [summary, categories, expenses, income, incomeEntries, greyZone, users] = await Promise.all([
          getMonthSummary(monthId),
          listCategories(monthId),
          listExpenses({ monthId }),
          getIncomeForMonth(monthId),
          listIncomeEntries(monthId),
          getGreyZone(monthId),
          this.users.length ? Promise.resolve(this.users) : listUsers(),
        ])
        this.summary = summary
        this.month = summary.month
        this.categories = categories
        this.expenses = expenses
        this.income = income
        this.incomeEntries = incomeEntries
        this.greyZone = greyZone
        this.users = users
      } finally {
        this.loading = false
      }
    },

    async refreshSummary() {
      if (this.monthId === null) return
      this.summary = await getMonthSummary(this.monthId)
    },

    async addCategory(payload: CategoryCreateRequest) {
      if (this.monthId === null) return
      const category = await apiCreateCategory(this.monthId, payload)
      this.categories.push(category)
      await this.refreshSummary()
    },

    async editCategory(categoryId: number, payload: CategoryUpdateRequest) {
      const updated = await apiUpdateCategory(categoryId, payload)
      this.categories = this.categories.map((c) => (c.id === categoryId ? updated : c))
      await this.refreshSummary()
    },

    async removeCategory(categoryId: number) {
      await apiDeleteCategory(categoryId)
      this.categories = this.categories.filter((c) => c.id !== categoryId)
      this.expenses = this.expenses.filter((e) => e.category_id !== categoryId)
      await this.refreshSummary()
    },

    async copyCategoriesFromPreviousMonth() {
      if (this.monthId === null) return
      const copied = await apiCopyCategoriesFromPrevious(this.monthId)
      this.categories = [...this.categories, ...copied]
      await this.refreshSummary()
    },

    async addExpense(payload: ExpenseCreateRequest) {
      const expense = await apiAddExpense(payload)
      this.expenses = [expense, ...this.expenses]
      await this.refreshSummary()
    },

    async removeExpense(expenseId: number) {
      await apiDeleteExpense(expenseId)
      this.expenses = this.expenses.filter((e) => e.id !== expenseId)
      await this.refreshSummary()
    },

    async setMyIncome(forecastAmount: string) {
      if (this.monthId === null) return
      const income = await apiSetMyIncome(this.monthId, { forecast_amount: forecastAmount })
      const idx = this.income.findIndex((i) => i.id === income.id)
      if (idx >= 0) {
        this.income[idx] = income
      } else {
        this.income.push(income)
      }
      await this.refreshSummary()
    },

    async addIncomeEntry(payload: IncomeEntryCreateRequest) {
      if (this.monthId === null) return
      const entry = await apiAddIncomeEntry(this.monthId, payload)
      this.incomeEntries = [entry, ...this.incomeEntries].sort((a, b) =>
        a.received_date === b.received_date ? b.id - a.id : b.received_date.localeCompare(a.received_date),
      )
      await this.refreshSummary()
    },

    async removeIncomeEntry(entryId: number) {
      await apiDeleteIncomeEntry(entryId)
      this.incomeEntries = this.incomeEntries.filter((e) => e.id !== entryId)
      await this.refreshSummary()
    },

    async setMyGreyZoneLimit(amount: string) {
      if (this.monthId === null) return
      const limit = await apiSetMyGreyZoneLimit(this.monthId, amount)
      this.greyZone.limits = [...this.greyZone.limits.filter((l) => l.id !== limit.id), limit]
      await this.refreshSummary()
    },

    async takeFromGreyZone(amount: string, takenDate: string) {
      if (this.monthId === null) return
      const entry = await apiTakeFromGreyZone(this.monthId, amount, takenDate)
      this.greyZone.entries = [entry, ...this.greyZone.entries]
      await this.refreshSummary()
    },

    async removeGreyZoneEntry(entryId: number) {
      await apiDeleteGreyZoneEntry(entryId)
      this.greyZone.entries = this.greyZone.entries.filter((e) => e.id !== entryId)
      await this.refreshSummary()
    },

    async setCarryover(amount: string | null) {
      if (this.monthId === null) return
      this.month = await apiSetCarryover(this.monthId, amount)
      await this.refreshSummary()
    },
  },
})
