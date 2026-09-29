import { apiClient } from './client'
import type { Month, MonthCreateRequest, MonthSummary } from '../types/models'

export function listMonths() {
  return apiClient.get<Month[]>('/months').then((r) => r.data)
}

export function createMonth(payload: MonthCreateRequest) {
  return apiClient.post<Month>('/months', payload).then((r) => r.data)
}

export function getMonthByYearMonth(year: number, month: number) {
  return apiClient.get<Month>(`/months/${year}/${month}`).then((r) => r.data)
}

export function getMonthSummary(monthId: number) {
  return apiClient.get<MonthSummary>(`/months/${monthId}/summary`).then((r) => r.data)
}

/** null goes back to carrying over the previous month's closing balance automatically. */
export function setCarryover(monthId: number, amount: string | null) {
  return apiClient.put<Month>(`/months/${monthId}/carryover`, { amount }).then((r) => r.data)
}
