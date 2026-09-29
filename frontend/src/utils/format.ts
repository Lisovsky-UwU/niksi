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

// Genitive case, for "на конец сентября".
const MONTH_NAMES_OF = [
  'января',
  'февраля',
  'марта',
  'апреля',
  'мая',
  'июня',
  'июля',
  'августа',
  'сентября',
  'октября',
  'ноября',
  'декабря',
]

export function monthOf(month: number): string {
  return MONTH_NAMES_OF[month - 1]
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

const shortDayFormatter = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' })

/** "2026-09-05" -> "5 сент." */
export function formatShortDate(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number)
  return shortDayFormatter.format(new Date(y, m - 1, d))
}

const longDateFormatter = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })

/** "2026-09-05" -> "5 сентября 2026 г." without the trailing "г." */
export function formatLongDate(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number)
  return longDateFormatter.format(new Date(y, m - 1, d)).replace(/\s?г\.$/, '')
}

/** "+1 500 ₽" / "−1 500 ₽" (a true minus sign), "0 ₽" for zero. */
export function formatSignedMoney(value: string | number | null | undefined): string {
  const n = toNumber(value)
  if (n === 0) return formatMoney(0)
  return `${n > 0 ? '+' : '−'}${formatMoney(Math.abs(n))}`
}

export function plural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return one
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few
  return many
}
