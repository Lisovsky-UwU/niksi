import { apiClient } from './client'
import type {
  SavingsPot,
  SavingsPotCreateRequest,
  SavingsPotUpdateRequest,
  SavingsTransfer,
  SavingsTransferCreateRequest,
} from '../types/models'

export function listPots(includeArchived = false) {
  return apiClient
    .get<SavingsPot[]>('/savings/pots', { params: { include_archived: includeArchived } })
    .then((r) => r.data)
}

export function createPot(payload: SavingsPotCreateRequest) {
  return apiClient.post<SavingsPot>('/savings/pots', payload).then((r) => r.data)
}

export function updatePot(potId: number, payload: SavingsPotUpdateRequest) {
  return apiClient.put<SavingsPot>(`/savings/pots/${potId}`, payload).then((r) => r.data)
}

export function deletePot(potId: number) {
  return apiClient.delete(`/savings/pots/${potId}`).then(() => undefined)
}

export function listTransfers(potId: number) {
  return apiClient.get<SavingsTransfer[]>(`/savings/pots/${potId}/transfers`).then((r) => r.data)
}

export function addTransfer(potId: number, payload: SavingsTransferCreateRequest) {
  return apiClient.post<SavingsTransfer>(`/savings/pots/${potId}/transfers`, payload).then((r) => r.data)
}

export function deleteTransfer(transferId: number) {
  return apiClient.delete(`/savings/transfers/${transferId}`).then(() => undefined)
}
