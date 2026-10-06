import type { Loan, LoanPaymentKind } from '../types/models'
import { formatShortDate, todayIso, toNumber } from './format'

export const PAYMENT_LABELS: Record<LoanPaymentKind, string> = {
  regular: 'Платеж',
  early: 'Досрочное погашение',
  correction: 'Поправка остатка',
}

/** Share of the debt already paid off, 0…1, counted from the debt the loan was added with. */
export function paidShare(loan: Loan): number {
  const principal = toNumber(loan.principal)
  if (principal <= 0) return 0
  return Math.min(1, Math.max(0, (principal - toNumber(loan.balance)) / principal))
}

/** The regular payment due now: the usual amount, or less when it is the last one (as the backend counts it). */
export function suggestedPayment(loan: Loan): number {
  const balance = toNumber(loan.balance)
  const interest = Math.round((balance * toNumber(loan.rate_percent)) / 12) / 100
  return Math.min(toNumber(loan.monthly_payment), Math.round((balance + interest) * 100) / 100)
}

/** "12.500" -> "12,5%" */
export function formatRate(rate: string): string {
  return `${toNumber(rate).toLocaleString('ru-RU', { maximumFractionDigits: 3 })}%`
}

export type DueState = 'overdue' | 'today' | 'soon' | 'later'

export function dueState(iso: string, today = todayIso()): DueState {
  if (iso < today) return 'overdue'
  if (iso === today) return 'today'
  const [y, m, d] = today.split('-').map(Number)
  const inThreeDays = new Date(y, m - 1, d + 3)
  const [dy, dm, dd] = iso.split('-').map(Number)
  return new Date(dy, dm - 1, dd) <= inThreeDays ? 'soon' : 'later'
}

/** "сегодня", "просрочен с 5 окт.", "15 окт." */
export function dueText(iso: string): string {
  const state = dueState(iso)
  if (state === 'today') return 'сегодня'
  if (state === 'overdue') return `просрочен с ${formatShortDate(iso)}`
  return formatShortDate(iso)
}
