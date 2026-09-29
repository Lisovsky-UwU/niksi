import type { SavingsPot, SavingsTransferDirection } from '../types/models'
import { toNumber } from './format'

export const KIND_LABELS = { account: 'Накопительный счёт', deposit: 'Вклад', goal: 'Цель' } as const

export const DIRECTION_LABELS: Record<SavingsTransferDirection, string> = {
  in: 'Отложили',
  out: 'Сняли',
  interest: 'Проценты',
}

/** The kind, unless the name already says it ("Накопительный счёт"). */
export function kindLabel(pot: SavingsPot): string {
  const kind = KIND_LABELS[pot.kind]
  return kind.toLowerCase() !== pot.name.trim().toLowerCase() ? kind : ''
}

export interface GoalStats {
  balance: number
  target: number
  reached: boolean
  /** Share of the target collected, 0…1 */
  share: number
  /** How much to put aside each month to make it by the date; null when not applicable. */
  monthly: { months: number; amount: number } | null
}

export function goalStats(pot: SavingsPot, now = new Date()): GoalStats {
  const balance = toNumber(pot.balance)
  const target = toNumber(pot.target_amount)
  const reached = target > 0 && balance >= target
  let monthly: GoalStats['monthly'] = null
  if (!pot.is_archived && pot.target_date && !reached && target > 0) {
    const [y, m] = pot.target_date.split('-').map(Number)
    const months = Math.max(1, (y - now.getFullYear()) * 12 + (m - (now.getMonth() + 1)))
    monthly = { months, amount: Math.ceil((target - balance) / months) }
  }
  return { balance, target, reached, share: target > 0 ? Math.min(1, balance / target) : 0, monthly }
}
