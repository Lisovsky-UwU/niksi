<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { getMonthSummary } from '../api/months'
import MonthCreateDialog from '../components/MonthCreateDialog.vue'
import { useMonthsStore } from '../stores/months'
import type { Month, MonthSummary } from '../types/models'
import { MONTH_NAMES, formatMoney, toNumber } from '../utils/format'

const store = useMonthsStore()
const router = useRouter()
const loading = ref(true)
const showCreateDialog = ref(false)
const summaries = ref(new Map<number, MonthSummary>())

const now = new Date()
const isCurrent = (m: Month) => m.year === now.getFullYear() && m.month === now.getMonth() + 1

const years = computed(() => {
  const sorted = [...store.months].sort((a, b) => b.year * 12 + b.month - (a.year * 12 + a.month))
  const groups: { year: number; months: Month[] }[] = []
  for (const m of sorted) {
    const last = groups[groups.length - 1]
    if (last && last.year === m.year) last.months.push(m)
    else groups.push({ year: m.year, months: [m] })
  }
  return groups
})

function stats(m: Month) {
  const s = summaries.value.get(m.id)
  if (!s) return null
  const limit = toNumber(s.totals.total_limit)
  const spent = toNumber(s.totals.total_spent)
  const hasIncome = toNumber(s.income.household_actual) > 0
  return {
    limit,
    spent,
    percent: limit > 0 ? Math.min((spent / limit) * 100, 100) : 0,
    over: limit > 0 && spent > limit,
    net: hasIncome ? toNumber(s.balance.net) : null,
  }
}

function handleCreated(m: Month) {
  showCreateDialog.value = false
  router.push({ name: 'dashboard', params: { year: m.year, month: m.month } })
}

onMounted(async () => {
  loading.value = true
  try {
    await store.loadMonths()
  } finally {
    loading.value = false
  }
  // Figures are a nice-to-have: a month whose summary fails still shows up as a plain link.
  const results = await Promise.allSettled(store.months.map((m) => getMonthSummary(m.id)))
  const map = new Map<number, MonthSummary>()
  results.forEach((r, i) => {
    if (r.status === 'fulfilled') map.set(store.months[i].id, r.value)
  })
  summaries.value = map
})
</script>

<template>
  <div class="history">
    <div class="page-head">
      <h1>Все месяцы</h1>
      <button
        class="btn btn-primary"
        type="button"
        :aria-expanded="showCreateDialog"
        @click="showCreateDialog = !showCreateDialog"
      >
        Новый месяц
      </button>
    </div>

    <MonthCreateDialog v-if="showCreateDialog" show-cancel @created="handleCreated" @cancel="showCreateDialog = false" />

    <p v-if="loading" class="muted">Загружаем месяцы…</p>
    <p v-else-if="years.length === 0" class="empty">
      Здесь будут все месяцы, которые вы ведёте. Создайте первый, чтобы начать записывать траты.
    </p>

    <section v-for="group in years" :key="group.year" class="year" :aria-labelledby="`year-${group.year}`">
      <h2 :id="`year-${group.year}`" class="year-title num">{{ group.year }}</h2>
      <ul class="months">
        <li v-for="m in group.months" :key="m.id">
          <RouterLink
            class="month-row"
            :class="{ current: isCurrent(m) }"
            :to="{ name: 'dashboard', params: { year: m.year, month: m.month } }"
          >
            <span class="name">
              {{ MONTH_NAMES[m.month - 1] }}
              <span v-if="isCurrent(m)" class="now">сейчас</span>
            </span>

            <template v-if="stats(m)">
              <span class="spent">
                <span class="bar" aria-hidden="true">
                  <span class="bar-fill" :class="{ over: stats(m)!.over }" :style="{ width: stats(m)!.percent + '%' }" />
                </span>
                <span class="num" :class="{ 'over-text': stats(m)!.over }">{{ formatMoney(stats(m)!.spent) }}</span>
                <span v-if="stats(m)!.limit > 0" class="num muted"> из {{ formatMoney(stats(m)!.limit) }}</span>
              </span>
              <span class="net num" :class="{ negative: (stats(m)!.net ?? 0) < 0 }">
                <template v-if="stats(m)!.net !== null">
                  {{ stats(m)!.net! >= 0 ? '+' : '−' }}{{ formatMoney(Math.abs(stats(m)!.net!)) }}
                </template>
                <span v-else class="muted">доход не указан</span>
              </span>
            </template>
          </RouterLink>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.history {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  max-width: 52rem;
}

.page-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding-top: 0.5rem;
}

.year {
  display: flex;
  flex-direction: column;
}

.year-title {
  font-size: 1.25rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--text);
}

.months {
  list-style: none;
  margin: 0;
  padding: 0;
}

.month-row {
  display: grid;
  grid-template-columns: 10rem minmax(0, 1fr) 9rem;
  align-items: center;
  gap: 0.5rem 1.5rem;
  padding: 0.9rem 0.75rem;
  margin: 0 -0.75rem;
  border-bottom: 1px solid var(--line);
  color: var(--text);
  text-decoration: none;
  border-radius: 0;
  transition: background-color 0.15s;
}

.month-row:hover {
  background: var(--ink-wash);
}

.name {
  font-weight: 600;
  font-size: 1.05rem;
}

.now {
  margin-left: 0.4rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--ink);
}

.current .name {
  color: var(--ink);
}

.spent {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.95rem;
}

.bar {
  flex: 0 0 5rem;
  height: 4px;
  border-radius: 2px;
  background: var(--line);
  overflow: hidden;
}

.bar-fill {
  display: block;
  height: 100%;
  background: var(--ink);
}

.bar-fill.over {
  background: var(--red);
}

.over-text {
  color: var(--red);
  font-weight: 600;
}

.net {
  text-align: right;
  font-weight: 600;
}

.net.negative {
  color: var(--red);
}

.net .muted {
  font-weight: 400;
  font-size: 0.875rem;
}

@media (max-width: 640px) {
  .month-row {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .spent {
    grid-column: 1 / -1;
    grid-row: 2;
  }

  .net {
    grid-row: 1;
    grid-column: 2;
  }
}
</style>
