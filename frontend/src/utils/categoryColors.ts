import type { CategoryColor } from '../types/models'

// The coloured pencils a category can be marked with. Their order matches the
// --cat-0…--cat-7 tokens in style.css and the automatic assignment by position.
export const CATEGORY_COLORS: { key: CategoryColor; label: string }[] = [
  { key: 'orange', label: 'Оранжевый' },
  { key: 'teal', label: 'Бирюзовый' },
  { key: 'violet', label: 'Фиолетовый' },
  { key: 'green', label: 'Зелёный' },
  { key: 'sky', label: 'Голубой' },
  { key: 'lilac', label: 'Лиловый' },
  { key: 'ochre', label: 'Охра' },
  { key: 'brown', label: 'Коричневый' },
]

export function categoryColorVar(key: CategoryColor): string {
  return `var(--cat-${CATEGORY_COLORS.findIndex((c) => c.key === key)})`
}
