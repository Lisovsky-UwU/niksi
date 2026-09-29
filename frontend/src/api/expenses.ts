import { apiClient } from './client'
import type { Expense, ExpenseCreateRequest, ExpenseUpdateRequest } from '../types/models'

export function listExpenses(params: { monthId?: number; categoryId?: number }) {
  return apiClient
    .get<Expense[]>('/expenses', {
      params: { month_id: params.monthId, category_id: params.categoryId },
    })
    .then((r) => r.data)
}

export function addExpense(payload: ExpenseCreateRequest) {
  return apiClient.post<Expense>('/expenses', payload).then((r) => r.data)
}

export function updateExpense(expenseId: number, payload: ExpenseUpdateRequest) {
  return apiClient.put<Expense>(`/expenses/${expenseId}`, payload).then((r) => r.data)
}

export function deleteExpense(expenseId: number) {
  return apiClient.delete(`/expenses/${expenseId}`).then(() => undefined)
}
