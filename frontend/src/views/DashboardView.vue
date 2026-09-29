<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterView } from 'vue-router'
import { getMonthByYearMonth } from '../api/months'
import MonthCreateDialog from '../components/MonthCreateDialog.vue'
import MonthPeriod from '../components/MonthPeriod.vue'
import MonthSelector from '../components/MonthSelector.vue'
import TabNav from '../components/TabNav.vue'
import { useBudgetStore } from '../stores/budget'
import { useMonthsStore } from '../stores/months'
import type { Month } from '../types/models'
import { monthLabel } from '../utils/format'

// Layout for one month: loads its data once, then each tab (overview, categories,
// expenses, income, grey zone) is a child route rendering its own part.
const props = defineProps<{ year: string; month: string }>()

const monthsStore = useMonthsStore()
const budgetStore = useBudgetStore()

const loading = ref(true)
const notFound = ref(false)

const yearNumber = computed(() => Number(props.year))
const monthNumber = computed(() => Number(props.month))

const tabs = computed(() => {
  const params = { year: props.year, month: props.month }
  return [
    { label: 'Обзор', to: { name: 'dashboard', params } },
    { label: 'Категории', to: { name: 'month-categories', params } },
    { label: 'Траты', to: { name: 'month-expenses', params } },
    { label: 'Доход', to: { name: 'month-income', params } },
    { label: 'Серая зона', to: { name: 'month-grey-zone', params } },
  ]
})

async function load() {
  loading.value = true
  notFound.value = false
  try {
    if (!monthsStore.loaded) {
      await monthsStore.loadMonths()
    }
    const month = await getMonthByYearMonth(yearNumber.value, monthNumber.value)
    await budgetStore.loadForMonth(month.id)
  } catch {
    notFound.value = true
  } finally {
    loading.value = false
  }
}

function handleCreated(month: Month) {
  notFound.value = false
  budgetStore.loadForMonth(month.id)
}

onMounted(load)
watch([yearNumber, monthNumber], load)
</script>

<template>
  <div>
    <p v-if="loading && !budgetStore.summary" class="muted loading">Открываем месяц…</p>

    <div v-else-if="notFound" class="not-found">
      <h1>{{ monthLabel(yearNumber, monthNumber) }} ещё не заведён</h1>
      <p class="muted">Создайте месяц, чтобы записывать в него траты и доход.</p>
      <MonthCreateDialog :initial-year="yearNumber" :initial-month="monthNumber" @created="handleCreated" />
    </div>

    <div v-else-if="budgetStore.summary" class="month" :class="{ refreshing: loading }">
      <div class="month-head">
        <MonthSelector :current-year="yearNumber" :current-month="monthNumber" />
        <MonthPeriod />
        <TabNav :tabs="tabs" label="Разделы месяца" />
      </div>
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.loading {
  padding: 3rem 0;
}

.not-found {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 28rem;
  padding: 2rem 0;
}

.month {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  transition: opacity 0.2s;
}

.month-head {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.month-head :deep(.month-selector) {
  margin-left: -0.6rem;
}

/* Single-block tabs read better at a comfortable width than stretched across the page. */
.month > :deep(.section) {
  width: 100%;
  max-width: 46rem;
}

.refreshing {
  opacity: 0.6;
}
</style>
