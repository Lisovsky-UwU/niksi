<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useBudgetStore } from '../stores/budget'
import type { Expense } from '../types/models'
import { formatDay, formatMoney, plural, toNumber } from '../utils/format'
import { periodOf } from '../utils/periods'
import ExpenseItem from './ExpenseItem.vue'

// Only the latest `limit` expenses are shown until "Показать все" is pressed:
// scrolling through a whole month on a phone is tiring. With `filterable` the list
// can be narrowed to some categories and a range of days.
const props = withDefaults(defineProps<{ limit?: number; title?: string; filterable?: boolean }>(), {
  limit: 10,
  title: 'Траты',
  filterable: false,
})

const store = useBudgetStore()
const showAll = ref(false)

// --- filters ---
const filtersOpen = ref(false)
const selectedCategories = ref<number[]>([])
const dateFrom = ref('')
const dateTo = ref('')

// The month's budget period, widened to any expense dated outside it, so none is unreachable.
const monthBounds = computed(() => {
  const m = store.month
  if (!m) return { min: '', max: '' }
  const period = periodOf(m)
  const dates = store.expenses.map((e) => e.expense_date)
  return {
    min: [period.start, ...dates].reduce((a, b) => (b < a ? b : a)),
    max: [period.end, ...dates].reduce((a, b) => (b > a ? b : a)),
  }
})

const activeFilterCount = computed(
  () => (selectedCategories.value.length ? 1 : 0) + (dateFrom.value || dateTo.value ? 1 : 0),
)

function resetFilters() {
  selectedCategories.value = []
  dateFrom.value = ''
  dateTo.value = ''
}

// Filters belong to the month being looked at.
watch(() => store.monthId, resetFilters)

const filtered = computed(() =>
  store.expenses.filter(
    (e) =>
      (!selectedCategories.value.length || selectedCategories.value.includes(e.category_id)) &&
      (!dateFrom.value || e.expense_date >= dateFrom.value) &&
      (!dateTo.value || e.expense_date <= dateTo.value),
  ),
)
const filteredTotal = computed(() => filtered.value.reduce((sum, e) => sum + toNumber(e.amount), 0))

// --- list ---
const hiddenCount = computed(() => Math.max(0, filtered.value.length - props.limit))
const visible = computed(() => (showAll.value ? filtered.value : filtered.value.slice(0, props.limit)))

// A day's total covers every expense of that day that passes the filters, even hidden ones.
const totalByDay = computed(() => {
  const totals = new Map<string, number>()
  for (const expense of filtered.value) {
    totals.set(expense.expense_date, (totals.get(expense.expense_date) ?? 0) + toNumber(expense.amount))
  }
  return totals
})

// The API already returns expenses newest first; group consecutive ones by day.
const days = computed(() => {
  const groups: { date: string; items: Expense[] }[] = []
  for (const expense of visible.value) {
    let group = groups[groups.length - 1]
    if (!group || group.date !== expense.expense_date) {
      group = { date: expense.expense_date, items: [] }
      groups.push(group)
    }
    group.items.push(expense)
  }
  return groups
})
</script>

<template>
  <section class="section" aria-labelledby="expenses-title">
    <div class="section-head">
      <h2 id="expenses-title">{{ props.title }}</h2>
      <button
        v-if="props.filterable && store.expenses.length"
        class="btn filter-toggle"
        :class="{ 'has-active': activeFilterCount }"
        type="button"
        :aria-expanded="filtersOpen"
        aria-controls="expense-filters"
        @click="filtersOpen = !filtersOpen"
      >
        <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2.5 3.5h11l-4.2 5v4l-2.6 1.2V8.5z" /></svg>
        Фильтры
        <span v-if="activeFilterCount" class="badge">{{ activeFilterCount }}</span>
      </button>
      <span v-else-if="store.expenses.length" class="muted">{{ store.expenses.length }} за месяц</span>
    </div>

    <div v-if="props.filterable && filtersOpen" id="expense-filters" class="filters">
      <fieldset class="filter-cats">
        <legend class="filter-label">Категории</legend>
        <label
          v-for="category in store.categories"
          :key="category.id"
          class="chip cat-chip"
          :style="{ '--cat': store.categoryColor(category.id) }"
        >
          <input v-model="selectedCategories" type="checkbox" :value="category.id" />
          <span>{{ category.name }}</span>
        </label>
      </fieldset>
      <div class="form-grid">
        <label class="field">
          С
          <input v-model="dateFrom" type="date" :min="monthBounds.min" :max="dateTo || monthBounds.max" />
        </label>
        <label class="field">
          По
          <input v-model="dateTo" type="date" :min="dateFrom || monthBounds.min" :max="monthBounds.max" />
        </label>
      </div>
      <button v-if="activeFilterCount" class="btn btn-quiet reset" type="button" @click="resetFilters">
        Сбросить фильтры
      </button>
    </div>

    <p v-if="props.filterable && activeFilterCount" class="found" role="status">
      <template v-if="filtered.length">
        Найдено {{ filtered.length }} {{ plural(filtered.length, 'трата', 'траты', 'трат') }} на
        <strong class="num">{{ formatMoney(filteredTotal) }}</strong>
      </template>
      <template v-else>
        Под эти фильтры ничего не подходит.
        <button class="link-btn" type="button" @click="resetFilters">Сбросить</button>
      </template>
    </p>

    <p v-if="store.expenses.length === 0" class="empty">В этом месяце ещё ничего не записано.</p>

    <div v-for="day in days" :key="day.date" class="day">
      <h3 class="day-head">
        <span>{{ formatDay(day.date) }}</span>
        <span class="num muted">{{ formatMoney(totalByDay.get(day.date) ?? 0) }}</span>
      </h3>
      <ul class="items">
        <ExpenseItem v-for="expense in day.items" :key="expense.id" :expense="expense" />
      </ul>
    </div>

    <button v-if="hiddenCount > 0" class="btn show-all" type="button" :aria-expanded="showAll" @click="showAll = !showAll">
      {{ showAll ? 'Свернуть' : `Показать все (ещё ${hiddenCount})` }}
    </button>
  </section>
</template>

<style scoped>
.section {
  gap: 0.25rem;
}

.filter-toggle {
  min-height: 2.25rem;
  padding: 0.3rem 0.8rem;
}

.filter-toggle svg {
  width: 0.95rem;
  height: 0.95rem;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.4;
  stroke-linejoin: round;
}

.filter-toggle.has-active {
  border-color: var(--ink);
  color: var(--ink);
}

.badge {
  display: inline-grid;
  place-items: center;
  min-width: 1.25rem;
  height: 1.25rem;
  padding: 0 0.3rem;
  border-radius: 999px;
  background: var(--ink);
  color: var(--on-ink);
  font-size: 0.75rem;
  font-weight: 600;
}

.filters {
  display: grid;
  gap: 0.85rem;
  margin: 0.75rem 0 0.25rem;
  padding: 1rem;
  background: var(--ink-wash);
  border-radius: 10px;
}

.filter-cats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0;
  padding: 0;
  border: none;
  min-width: 0;
}

.filter-label {
  width: 100%;
  padding: 0;
  margin-bottom: 0.4rem;
  font-size: 0.875rem;
  color: var(--muted);
}

.reset {
  justify-self: start;
  margin-left: -0.5rem;
}

.found {
  margin-top: 0.75rem;
  color: var(--muted);
}

.found strong {
  color: var(--text);
  font-weight: 600;
}

.link-btn {
  border: none;
  background: none;
  padding: 0;
  color: var(--ink);
  font-weight: 500;
  cursor: pointer;
  text-decoration: underline;
}

.day {
  padding-top: 1rem;
}

.show-all {
  margin-top: 1rem;
  align-self: stretch;
}

.day-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 0.95rem;
  font-weight: 600;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--line);
}

.day-head .muted {
  font-weight: 500;
}

.items {
  list-style: none;
  margin: 0;
  padding: 0;
}
</style>
