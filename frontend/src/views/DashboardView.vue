<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getMonthByYearMonth } from '../api/months'
import CategoryList from '../components/CategoryList.vue'
import ExpenseList from '../components/ExpenseList.vue'
import IncomePanel from '../components/IncomePanel.vue'
import MonthCreateDialog from '../components/MonthCreateDialog.vue'
import MonthHero from '../components/MonthHero.vue'
import { useBudgetStore } from '../stores/budget'
import { useMonthsStore } from '../stores/months'
import type { Month } from '../types/models'
import { monthLabel } from '../utils/format'

const props = defineProps<{ year: string; month: string }>()

const monthsStore = useMonthsStore()
const budgetStore = useBudgetStore()

const loading = ref(true)
const notFound = ref(false)

const yearNumber = computed(() => Number(props.year))
const monthNumber = computed(() => Number(props.month))

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

    <div v-else-if="budgetStore.summary" class="dashboard" :class="{ refreshing: loading }">
      <MonthHero :summary="budgetStore.summary" />

      <div class="columns">
        <CategoryList />
        <div class="side">
          <IncomePanel />
          <ExpenseList />
        </div>
      </div>
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

.dashboard {
  display: flex;
  flex-direction: column;
  gap: 3rem;
  transition: opacity 0.2s;
}

.refreshing {
  opacity: 0.6;
}

.columns {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
  gap: 3rem;
  align-items: start;
}

.side {
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

@media (max-width: 860px) {
  .columns {
    grid-template-columns: 1fr;
  }
}
</style>
