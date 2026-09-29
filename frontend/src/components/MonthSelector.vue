<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMonthsStore } from '../stores/months'
import { monthLabel } from '../utils/format'

const props = defineProps<{ currentYear: number; currentMonth: number }>()
const store = useMonthsStore()
const router = useRouter()
const route = useRoute()

const sortedMonths = computed(() =>
  [...store.months].sort((a, b) => (a.year === b.year ? a.month - b.month : a.year - b.year)),
)

const currentIndex = computed(() =>
  sortedMonths.value.findIndex((m) => m.year === props.currentYear && m.month === props.currentMonth),
)

const prev = computed(() => (currentIndex.value > 0 ? sortedMonths.value[currentIndex.value - 1] : null))
const next = computed(() =>
  currentIndex.value >= 0 && currentIndex.value < sortedMonths.value.length - 1
    ? sortedMonths.value[currentIndex.value + 1]
    : null,
)

// The dropdown lists the newest month first, going back in time.
const newestFirst = computed(() => [...sortedMonths.value].reverse())

// Stay on the same tab (expenses, income…) when switching months.
function go(year: number, month: number) {
  const name = typeof route.name === 'string' && route.name.startsWith('month-') ? route.name : 'dashboard'
  router.push({ name, params: { year, month } })
}

function handleChange(event: Event) {
  const [year, month] = (event.target as HTMLSelectElement).value.split('-').map(Number)
  go(year, month)
}
</script>

<template>
  <div class="month-selector">
    <button
      class="step"
      type="button"
      :disabled="!prev"
      :aria-label="prev ? `Предыдущий месяц: ${monthLabel(prev.year, prev.month)}` : 'Предыдущего месяца нет'"
      @click="prev && go(prev.year, prev.month)"
    >
      <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3 5 8l5 5" /></svg>
    </button>

    <label class="current">
      <span class="visually-hidden">Месяц</span>
      <select :value="`${props.currentYear}-${props.currentMonth}`" @change="handleChange">
        <option v-for="m in newestFirst" :key="m.id" :value="`${m.year}-${m.month}`">
          {{ monthLabel(m.year, m.month) }}
        </option>
      </select>
    </label>

    <button
      class="step"
      type="button"
      :disabled="!next"
      :aria-label="next ? `Следующий месяц: ${monthLabel(next.year, next.month)}` : 'Следующего месяца нет'"
      @click="next && go(next.year, next.month)"
    >
      <svg viewBox="0 0 16 16" aria-hidden="true"><path d="m6 3 5 5-5 5" /></svg>
    </button>
  </div>
</template>

<style scoped>
.month-selector {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.step {
  display: grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--text);
  cursor: pointer;
}

.step svg {
  width: 1rem;
  height: 1rem;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.step:hover:not(:disabled) {
  background: var(--ink-wash);
  color: var(--ink);
}

.step:disabled {
  opacity: 0.3;
  cursor: default;
}

.current select {
  width: auto;
  min-height: 0;
  padding: 0.2rem 0.4rem;
  border-color: transparent;
  background: transparent;
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  cursor: pointer;
}

.current select:hover {
  border-color: var(--line);
  background: var(--sheet);
}
</style>
