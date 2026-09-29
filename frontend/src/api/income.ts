import { apiClient } from './client'
import type { Income, IncomeSetRequest } from '../types/models'

export function getIncomeForMonth(monthId: number) {
  return apiClient.get<Income[]>(`/months/${monthId}/income`).then((r) => r.data)
}

export function setMyIncome(monthId: number, payload: IncomeSetRequest) {
  return apiClient.put<Income>(`/months/${monthId}/income/me`, payload).then((r) => r.data)
}
