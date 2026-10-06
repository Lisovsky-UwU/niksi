import { apiClient } from './client'
import type { Loan, LoanCreateRequest, LoanPayment, LoanPaymentCreateRequest, LoanUpdateRequest } from '../types/models'

export function listLoans() {
  return apiClient.get<Loan[]>('/loans').then((r) => r.data)
}

export function createLoan(payload: LoanCreateRequest) {
  return apiClient.post<Loan>('/loans', payload).then((r) => r.data)
}

export function updateLoan(loanId: number, payload: LoanUpdateRequest) {
  return apiClient.put<Loan>(`/loans/${loanId}`, payload).then((r) => r.data)
}

export function deleteLoan(loanId: number) {
  return apiClient.delete(`/loans/${loanId}`).then(() => undefined)
}

export function listPayments(loanId: number) {
  return apiClient.get<LoanPayment[]>(`/loans/${loanId}/payments`).then((r) => r.data)
}

export function addPayment(loanId: number, payload: LoanPaymentCreateRequest) {
  return apiClient.post<LoanPayment>(`/loans/${loanId}/payments`, payload).then((r) => r.data)
}

export function deletePayment(paymentId: number) {
  return apiClient.delete(`/loans/payments/${paymentId}`).then(() => undefined)
}
