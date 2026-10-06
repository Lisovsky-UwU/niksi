<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import type { Loan } from '../types/models'
import { formatMoney } from '../utils/format'
import { dueState, dueText, paidShare, suggestedPayment } from '../utils/loans'
import GoalCells from './GoalCells.vue'

// A loan in the list: what is still owed, the next payment, and how much is paid off.
const props = defineProps<{ loan: Loan }>()
const share = computed(() => paidShare(props.loan))
const due = computed(() => (props.loan.next_payment_date ? dueState(props.loan.next_payment_date) : null))
</script>

<template>
  <li>
    <RouterLink :to="{ name: 'money-loan', params: { loanId: loan.id } }" class="loan">
      <span class="title">
        <span class="name">{{ loan.name }}</span>
        <span v-if="loan.is_closed" class="meta">Закрыт</span>
        <span v-else-if="loan.next_payment_date" class="meta" :class="`due-${due}`">
          Платеж {{ formatMoney(suggestedPayment(loan)) }}, {{ dueText(loan.next_payment_date) }}
        </span>
        <span v-else class="meta">Долг выплачен</span>
      </span>
      <span class="num balance">{{ formatMoney(loan.balance) }}</span>
      <svg class="chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="m6 3 5 5-5 5" /></svg>

      <span v-if="!loan.is_closed" class="paid">
        <GoalCells :share="share" :label="`Выплачено ${Math.floor(share * 100)}% долга`" />
        <span class="meta">выплачено {{ Math.floor(share * 100) }}%</span>
      </span>
    </RouterLink>
  </li>
</template>

<style scoped>
.loan {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto 1rem;
  align-items: center;
  gap: 0.5rem 0.75rem;
  padding: 0.85rem 0.75rem;
  margin: 0 -0.75rem;
  border-bottom: 1px solid var(--line);
  border-radius: 10px;
  color: var(--text);
  text-decoration: none;
  transition: background-color 0.15s;
}

li:last-child .loan {
  border-bottom: none;
}

.loan:hover {
  background: var(--ink-wash);
}

.title {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.name {
  font-weight: 600;
  font-size: 1.05rem;
  overflow-wrap: anywhere;
}

.due-overdue {
  color: var(--red);
  font-weight: 500;
}

.due-today,
.due-soon {
  color: var(--loan);
  font-weight: 500;
}

.balance {
  font-weight: 600;
  font-size: 1.1rem;
}

.chevron {
  width: 1rem;
  height: 1rem;
  fill: none;
  stroke: var(--muted);
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.loan:hover .chevron {
  stroke: var(--ink);
}

.paid {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 0.75rem;
}
</style>
