// Amounts arrive from the API as decimal strings ("1500.50"); these helpers
// turn them into Russian-formatted text for display only.

const moneyFormatter = new Intl.NumberFormat('ru-RU', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
})

export function toNumber(value: string | number | null | undefined): number {
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}

/** "1500.5" -> "1 500,5 ₽" */
export function formatMoney(value: string | number | null | undefined): string {
  return `${moneyFormatter.format(toNumber(value))} ₽`
}

/** Same as formatMoney but without the currency sign, for large figures styled separately. */
export function formatAmount(value: string | number | null | undefined): string {
  return moneyFormatter.format(toNumber(value))
}

export const MONTH_NAMES = [
  'Январь',
  'Февраль',
  'Март',
  'Апрель',
  'Май',
  'Июнь',
  'Июль',
  'Август',
  'Сентябрь',
  'Октябрь',
  'Ноябрь',
  'Декабрь',
]

// Prepositional case, for "в сентябре".
const MONTH_NAMES_IN = [
  'январе',
  'феврале',
  'марте',
  'апреле',
  'мае',
  'июне',
  'июле',
  'августе',
  'сентябре',
  'октябре',
  'ноябре',
  'декабре',
]

export function monthLabel(year: number, month: number): string {
  return `${MONTH_NAMES[month - 1]} ${year}`
}

export function monthIn(month: number): string {
  return MONTH_NAMES_IN[month - 1]
}

export function todayIso(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function shiftIso(iso: string, days: number): string {
  const [y, m, d] = iso.split('-').map(Number)
  const date = new Date(y, m - 1, d + days)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

const dayFormatter = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', weekday: 'long' })

/** "2026-09-29" -> "Сегодня" / "Вчера" / "27 сентября, воскресенье" */
export function formatDay(iso: string): string {
  const today = todayIso()
  if (iso === today) return 'Сегодня'
  if (iso === shiftIso(today, -1)) return 'Вчера'
  const [y, m, d] = iso.split('-').map(Number)
  const parts = dayFormatter.formatToParts(new Date(y, m - 1, d))
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? ''
  return `${get('day')} ${get('month')}, ${get('weekday')}`
}
