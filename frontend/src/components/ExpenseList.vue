<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useBudgetStore } from '../stores/budget'
import type { Expense } from '../types/models'
import { formatDay, formatMoney, toNumber } from '../utils/format'
import ConfirmButton from './ConfirmButton.vue'

const store = useBudgetStore()
const auth = useAuthStore()

const categoryNameById = computed(() => {
  const map = new Map<number, string>()
  for (const category of store.categories) {
    map.set(category.id, category.name)
  }
  return map
})

// Only people who entered income appear in the summary, so the partner's name may be unknown.
const nameByUserId = computed(() => {
  const map = new Map<number, string>()
  for (const entry of store.summary?.income.per_user ?? []) {
    map.set(entry.user_id, entry.display_name)
  }
  return map
})

function author(expense: Expense): string | null {
  if (expense.created_by_user_id === auth.user?.id) return 'вы'
  return nameByUserId.value.get(expense.created_by_user_id) ?? null
}

// The API already returns expenses newest first; group consecutive ones by day.
const days = computed(() => {
  const groups: { date: string; total: number; items: Expense[] }[] = []
  for (const expense of store.expenses) {
    let group = groups[groups.length - 1]
    if (!group || group.date !== expense.expense_date) {
      group = { date: expense.expense_date, total: 0, items: [] }
      groups.push(group)
    }
    group.items.push(expense)
    group.total += toNumber(expense.amount)
  }
  return groups
})

async function handleRemove(expenseId: number) {
  await store.removeExpense(expenseId)
}
</script>

<template>
  <section class="section" aria-labelledby="expenses-title">
    <div class="section-head">
      <h2 id="expenses-title">Траты</h2>
      <span v-if="store.expenses.length" class="muted">{{ store.expenses.length }} за месяц</span>
    </div>

    <p v-if="store.expenses.length === 0" class="empty">
      В этом месяце ещё ничего не записано. Первая трата добавляется в форме наверху.
    </p>

    <div v-for="day in days" :key="day.date" class="day">
      <h3 class="day-head">
        <span>{{ formatDay(day.date) }}</span>
        <span class="num muted">{{ formatMoney(day.total) }}</span>
      </h3>
      <ul class="items">
        <li v-for="expense in day.items" :key="expense.id" class="item">
          <div class="what">
            <span class="category">{{ categoryNameById.get(expense.category_id) ?? 'Без категории' }}</span>
            <span v-if="expense.description || author(expense)" class="details muted">
              <span v-if="expense.description">{{ expense.description }}</span>
              <span v-if="author(expense)" class="author">{{ author(expense) }}</span>
            </span>
          </div>
          <span class="num amount">{{ formatMoney(expense.amount) }}</span>
          <ConfirmButton class="remove" confirm-label="Удалить трату" @confirm="handleRemove(expense.id)" />
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.section {
  gap: 0.25rem;
}

.day {
  padding-top: 1rem;
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

.item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 0.25rem 1rem;
  padding: 0.55rem 0;
  border-bottom: 1px dashed var(--line);
}

.item:last-child {
  border-bottom: none;
}

.what {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.category {
  font-weight: 500;
}

.details {
  display: flex;
  flex-wrap: wrap;
  gap: 0 0.75rem;
  font-size: 0.875rem;
  overflow-wrap: anywhere;
}

.author {
  font-style: italic;
}

.amount {
  font-weight: 600;
  text-align: right;
}

@media (hover: hover) {
  .remove {
    opacity: 0;
    transition: opacity 0.15s;
  }

  .item:hover .remove,
  .remove:focus-within {
    opacity: 1;
  }
}

@media (max-width: 560px) {
  .item {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .remove {
    grid-column: 1 / -1;
    justify-self: end;
    margin-top: -0.25rem;
  }
}
</style>
