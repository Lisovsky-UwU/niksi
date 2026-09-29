import { apiClient } from './client'
import type { BalanceStatus, Reconciliation, ReconciliationCreateRequest } from '../types/models'

export function getBalance() {
  return apiClient.get<BalanceStatus>('/balance').then((r) => r.data)
}

export function listReconciliations() {
  return apiClient.get<Reconciliation[]>('/reconciliations').then((r) => r.data)
}

export function createReconciliation(payload: ReconciliationCreateRequest) {
  return apiClient.post<Reconciliation>('/reconciliations', payload).then((r) => r.data)
}

export function deleteReconciliation(id: number) {
  return apiClient.delete(`/reconciliations/${id}`).then(() => undefined)
}
