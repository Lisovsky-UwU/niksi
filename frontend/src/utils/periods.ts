import type { Month } from '../types/models'
import { todayIso } from './format'

// A budget month is a period: from the day of the first full salary until the day before
// the next month starts. The latest month has no end yet, so it is estimated as a month on.

function addDays(iso: string, days: number): string {
  const [y, m, d] = iso.split('-').map(Number)
  const date = new Date(y, m - 1, d + days)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/** Same day a month later, minus one day (clamped for short months). */
function estimatedEnd(start: string): string {
  const [y, m, d] = start.split('-').map(Number)
  const lastDayNext = new Date(y, m + 1, 0).getDate()
  const next = new Date(y, m, Math.min(d, lastDayNext))
  const pad = (n: number) => String(n).padStart(2, '0')
  return addDays(`${next.getFullYear()}-${pad(next.getMonth() + 1)}-${pad(next.getDate())}`, -1)
}

export interface Period {
  start: string
  end: string
  /** true while no next month exists and the end is only a guess */
  estimated: boolean
}

export function periodOf(month: Pick<Month, 'start_date' | 'end_date'>): Period {
  return month.end_date
    ? { start: month.start_date, end: month.end_date, estimated: false }
    : { start: month.start_date, end: estimatedEnd(month.start_date), estimated: true }
}

/** The month whose period today falls into: the latest one that has already started. */
export function currentMonth(months: Month[], today = todayIso()): Month | null {
  return (
    [...months]
      .filter((m) => m.start_date <= today)
      .sort((a, b) => b.start_date.localeCompare(a.start_date))[0] ?? null
  )
}

export function isCurrent(month: Month, today = todayIso()): boolean {
  const { start, end, estimated } = periodOf(month)
  return start <= today && (estimated || today <= end)
}

/** Whole days left in the period, today included; null when today is outside it. */
export function daysLeft(month: Month, today = todayIso()): number | null {
  const { start, end } = periodOf(month)
  if (today < start || today > end) return null
  const [ty, tm, td] = today.split('-').map(Number)
  const [ey, em, ed] = end.split('-').map(Number)
  return Math.round((Date.UTC(ey, em - 1, ed) - Date.UTC(ty, tm - 1, td)) / 86_400_000) + 1
}

/** The range a month may start in: the 1st of the previous calendar month to the end of its own. */
export function allowedStartRange(year: number, month: number): { min: string; max: string } {
  const pad = (n: number) => String(n).padStart(2, '0')
  const prevYear = month === 1 ? year - 1 : year
  const prevMonth = month === 1 ? 12 : month - 1
  const last = new Date(year, month, 0).getDate()
  return { min: `${prevYear}-${pad(prevMonth)}-01`, max: `${year}-${pad(month)}-${pad(last)}` }
}
