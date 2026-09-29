<script setup lang="ts">
import { computed } from 'vue'
import type { MonthSummary } from '../types/models'
import { formatAmount, formatMoney, monthIn, toNumber } from '../utils/format'
import ExpenseForm from './ExpenseForm.vue'
import MonthSelector from './MonthSelector.vue'

const props = defineProps<{ summary: MonthSummary }>()

const limit = computed(() => toNumber(props.summary.totals.total_limit))
const spent = computed(() => toNumber(props.summary.totals.total_spent))
const left = computed(() => limit.value - spent.value)

const state = computed<'no-limits' | 'ok' | 'over'>(() => {
  if (limit.value <= 0) return 'no-limits'
  return left.value >= 0 ? 'ok' : 'over'
})

const headline = computed(() => {
  const inMonth = monthIn(props.summary.month.month)
  if (state.value === 'no-limits') return `Потрачено в ${inMonth}`
  if (state.value === 'over') return `Перерасход в ${inMonth}`
  return `Осталось в ${inMonth}`
})

const figure = computed(() => {
  if (state.value === 'no-limits') return spent.value
  return Math.abs(left.value)
})

const usedPercent = computed(() => (limit.value > 0 ? Math.min((spent.value / limit.value) * 100, 100) : 0))

function plural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return one
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few
  return many
}

// Only meaningful while the month is still running: how much per day is left to spend.
const perDay = computed(() => {
  if (state.value !== 'ok') return null
  const now = new Date()
  const { year, month } = props.summary.month
  if (now.getFullYear() !== year || now.getMonth() + 1 !== month) return null
  const daysInMonth = new Date(year, month, 0).getDate()
  const daysLeft = daysInMonth - now.getDate() + 1
  return {
    days: daysLeft,
    daysWord: plural(daysLeft, 'день', 'дня', 'дней'),
    amount: Math.floor(left.value / daysLeft),
  }
})
</script>

<template>
  <section class="hero grid-paper" aria-labelledby="hero-headline">
    <div class="hero-top">
      <MonthSelector :current-year="summary.month.year" :current-month="summary.month.month" />
    </div>

    <div class="hero-body">
      <div class="figures">
        <h1 id="hero-headline" class="headline">{{ headline }}</h1>
        <p
          :key="`${summary.month.id}-${state}`"
          class="figure hand num"
          :class="{ 'figure-over': state === 'over' }"
        >
          {{ formatAmount(figure) }}<span class="figure-currency">₽</span>
        </p>

        <template v-if="state !== 'no-limits'">
          <div
            class="meter"
            role="meter"
            :aria-valuenow="Math.round(usedPercent)"
            aria-valuemin="0"
            aria-valuemax="100"
            aria-label="Доля потраченного от общего лимита"
          >
            <div class="meter-fill" :class="{ 'meter-over': state === 'over' }" :style="{ width: usedPercent + '%' }" />
          </div>
          <p class="context">
            Потрачено <strong class="num">{{ formatMoney(spent) }}</strong> из
            <span class="num">{{ formatMoney(limit) }}</span> по всем категориям.
          </p>
        </template>
        <p v-else class="context">Задайте категориям лимиты, и здесь появится остаток на месяц.</p>

        <p v-if="perDay" class="context">
          До конца месяца {{ perDay.days }} {{ perDay.daysWord }}, это примерно
          <strong class="num">{{ formatMoney(perDay.amount) }}</strong> в день.
        </p>
      </div>

      <ExpenseForm class="hero-form" />
    </div>
  </section>
</template>

<style scoped>
.hero {
  position: relative;
  border: 1px solid var(--line);
  border-radius: var(--radius-sheet);
  padding: 0.75rem 1.5rem 2rem calc(var(--cell) * 3 + 1.25rem);
  overflow: hidden;
}

/* The red margin line of a school notebook. */
.hero::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: calc(var(--cell) * 3);
  width: 2px;
  background: var(--margin);
}

.hero-top {
  margin-left: -0.6rem;
  margin-bottom: 1rem;
}

.hero-body {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  gap: 2rem 3rem;
  align-items: start;
}

.figures {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-top: 0.5rem;
}

.headline {
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: 0;
}

.figure {
  font-size: clamp(4.5rem, 11vw, 7.5rem);
  margin: -0.25rem 0 0.25rem -0.2rem;
  animation: write-in 0.9s cubic-bezier(0.55, 0, 0.3, 1) both;
}

.figure-currency {
  font-size: 0.55em;
  margin-left: 0.15em;
}

.figure-over {
  color: var(--red);
}

@keyframes write-in {
  from {
    clip-path: inset(-20% 100% -20% 0);
  }
  to {
    clip-path: inset(-20% -5% -20% 0);
  }
}

.meter {
  height: 6px;
  max-width: 26rem;
  border-radius: 3px;
  background: color-mix(in srgb, var(--line) 70%, transparent);
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  background: var(--ink);
  border-radius: inherit;
  transition: width 0.4s ease;
}

.meter-over {
  background: var(--red);
}

.context {
  max-width: 30rem;
  color: var(--muted);
}

.context strong {
  color: var(--text);
  font-weight: 600;
}

@media (max-width: 860px) {
  .hero-body {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .hero {
    padding: 0.5rem 1rem 1.5rem calc(var(--cell) * 1 + 1rem);
  }

  .hero::before {
    left: var(--cell);
  }
}
</style>
