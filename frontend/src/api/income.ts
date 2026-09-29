import { apiClient } from './client'
import type { Income, IncomeEntry, IncomeEntryCreateRequest, IncomeSetRequest } from '../types/models'

export function getIncomeForMonth(monthId: number) {
  return apiClient.get<Income[]>(`/months/${monthId}/income`).then((r) => r.data)
}

export function setMyIncome(monthId: number, payload: IncomeSetRequest) {
  return apiClient.put<Income>(`/months/${monthId}/income/me`, payload).then((r) => r.data)
}

export function listIncomeEntries(monthId: number) {
  return apiClient.get<IncomeEntry[]>(`/months/${monthId}/income/entries`).then((r) => r.data)
}

export function addIncomeEntry(monthId: number, payload: IncomeEntryCreateRequest) {
  return apiClient.post<IncomeEntry>(`/months/${monthId}/income/entries`, payload).then((r) => r.data)
}

export function deleteIncomeEntry(entryId: number) {
  return apiClient.delete(`/income-entries/${entryId}`).then(() => undefined)
}
