<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useBudgetStore } from '../stores/budget'
import { formatMoney, todayIso } from '../utils/format'
import GrowingTextarea from './GrowingTextarea.vue'
import PersonPicker from './PersonPicker.vue'

const store = useBudgetStore()
const auth = useAuthStore()
// Who spent the money: whoever records it, unless they pick the other person.
const spentBy = ref<number | null>(auth.user?.id ?? null)
const route = useRoute()

const categoryId = ref<number | null>(store.categories[0]?.id ?? null)

// Categories can load or get added after this form is already mounted (e.g. the
// list arrives asynchronously, or the user adds the first category via
// CategoryList) — keep the selection valid as that list changes.
watch(
  () => store.categories,
  (categories) => {
    if (categoryId.value === null || !categories.some((c) => c.id === categoryId.value)) {
      categoryId.value = categories[0]?.id ?? null
    }
  },
  { deep: true },
)

const amount = ref('')
const description = ref('')
const expenseDate = ref(todayIso())
const submitting = ref(false)
const error = ref('')
const lastSaved = ref('')

const selectedSummary = computed(
  () => store.summary?.categories.find((c) => c.id === categoryId.value) ?? null,
)

async function handleSubmit() {
  if (!categoryId.value || !amount.value) return
  error.value = ''
  submitting.value = true
  try {
    const categoryName = store.categories.find((c) => c.id === categoryId.value)?.name ?? ''
    await store.addExpense({
      category_id: categoryId.value,
      amount: amount.value,
      description: description.value.trim() || null,
      expense_date: expenseDate.value,
      spent_by_user_id: spentBy.value ?? undefined,
    })
    lastSaved.value = `Записано: ${formatMoney(amount.value)} в «${categoryName}»`
    amount.value = ''
    description.value = ''
    spentBy.value = auth.user?.id ?? null
  } catch {
    error.value = 'Трата не сохранилась. Проверьте сумму и попробуйте ещё раз.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form class="expense-form" @submit.prevent="handleSubmit">
    <h2 class="form-title">Записать трату</h2>

    <p v-if="store.categories.length === 0" class="no-categories">
      Сначала заведите хотя бы одну категорию, чтобы было куда записывать траты.
      <RouterLink :to="{ name: 'month-categories', params: route.params }">Перейти к категориям</RouterLink>
    </p>

    <template v-else>
      <label class="amount">
        <span class="visually-hidden">Сумма в рублях</span>
        <input
          v-model="amount"
          type="number"
          inputmode="decimal"
          min="0.01"
          step="0.01"
          placeholder="0"
          required
        />
        <span class="amount-currency" aria-hidden="true">₽</span>
      </label>

      <fieldset class="chips">
        <legend class="visually-hidden">Категория</legend>
        <label
          v-for="category in store.categories"
          :key="category.id"
          class="chip cat-chip"
          :style="{ '--cat': store.categoryColor(category.id) }"
        >
          <input v-model="categoryId" type="radio" name="expense-category" :value="category.id" />
          <span>{{ category.name }}</span>
        </label>
      </fieldset>
      <p v-if="selectedSummary" class="category-left muted">
        В «{{ selectedSummary.name }}» осталось
        <span class="num" :class="{ over: Number(selectedSummary.remaining) < 0 }">
          {{ formatMoney(selectedSummary.remaining) }}
        </span>
      </p>

      <PersonPicker
        v-if="store.users.length > 1"
        v-model="spentBy"
        :users="store.users"
        :me-id="auth.user?.id"
        label="Кто потратил"
        name="expense-spent-by"
      />
      <label class="field">
        На что потратили
        <GrowingTextarea v-model="description" placeholder="Необязательно: пара слов или пара предложений" />
      </label>
      <label class="field date">
        Дата
        <input v-model="expenseDate" type="date" required />
      </label>

      <button class="btn btn-primary submit" type="submit" :disabled="submitting || !amount">
        {{ submitting ? 'Записываем…' : 'Записать' }}
      </button>

      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <p v-else-if="lastSaved" :key="lastSaved" class="saved" role="status">{{ lastSaved }}</p>
    </template>
  </form>
</template>

<style scoped>
.expense-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.25rem;
  background: var(--sheet);
  border: 1px solid var(--line);
  border-radius: 12px;
}

.form-title {
  font-size: 1.125rem;
}

.no-categories {
  color: var(--muted);
}

.amount {
  position: relative;
  display: block;
}

.amount input {
  font-size: 2rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  padding: 0.35rem 2.5rem 0.35rem 0.75rem;
  min-height: 3.5rem;
  /* Hide number spinners: they fight with a large figure. */
  appearance: textfield;
  -moz-appearance: textfield;
}

.amount input::-webkit-outer-spin-button,
.amount input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.amount-currency {
  position: absolute;
  right: 0.9rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.5rem;
  color: var(--muted);
  pointer-events: none;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0;
  padding: 0;
  border: none;
}

.category-left {
  font-size: 0.875rem;
}

.category-left .num {
  color: var(--text);
  font-weight: 600;
}

.category-left .over {
  color: var(--red);
}

.date {
  max-width: 12rem;
}

.submit {
  align-self: flex-start;
  min-width: 9rem;
}

.saved {
  font-size: 0.9rem;
  color: var(--ink);
  animation: saved-in 0.3s ease both;
}

@keyframes saved-in {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
}

@media (max-width: 420px) {

  .submit {
    align-self: stretch;
  }
}
</style>
