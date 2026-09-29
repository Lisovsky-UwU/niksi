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
import { getIncomeForMonth, setMyIncome as apiSetMyIncome } from '../api/income'
import { getMonthSummary } from '../api/months'
import type {
  Category,
  CategoryCreateRequest,
  CategoryUpdateRequest,
  Expense,
  ExpenseCreateRequest,
  Income,
  IncomeSetRequest,
  Month,
  MonthSummary,
} from '../types/models'

export const useBudgetStore = defineStore('budget', {
  state: () => ({
    monthId: null as number | null,
    month: null as Month | null,
    summary: null as MonthSummary | null,
    categories: [] as Category[],
    expenses: [] as Expense[],
    income: [] as Income[],
    loading: false,
  }),
  actions: {
    async loadForMonth(monthId: number) {
      this.loading = true
      this.monthId = monthId
      try {
        const [summary, categories, expenses, income] = await Promise.all([
          getMonthSummary(monthId),
          listCategories(monthId),
          listExpenses({ monthId }),
          getIncomeForMonth(monthId),
        ])
        this.summary = summary
        this.month = summary.month
        this.categories = categories
        this.expenses = expenses
        this.income = income
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

    async setMyIncome(payload: IncomeSetRequest) {
      if (this.monthId === null) return
      const income = await apiSetMyIncome(this.monthId, payload)
      const idx = this.income.findIndex((i) => i.id === income.id)
      if (idx >= 0) {
        this.income[idx] = income
      } else {
        this.income.push(income)
      }
      await this.refreshSummary()
    },
  },
})
