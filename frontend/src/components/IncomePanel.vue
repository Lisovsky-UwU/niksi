<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useBudgetStore } from '../stores/budget'
import { formatMoney, toNumber } from '../utils/format'

const auth = useAuthStore()
const store = useBudgetStore()

const myIncome = computed(() => store.income.find((i) => i.user_id === auth.user?.id) ?? null)

const forecastAmount = ref('')
const actualAmount = ref('')
const submitting = ref(false)
const editing = ref(false)
const error = ref('')

watch(
  myIncome,
  (income) => {
    forecastAmount.value = income?.forecast_amount ?? ''
    actualAmount.value = income?.actual_amount ?? ''
  },
  { immediate: true },
)

const perUser = computed(() => store.summary?.income.per_user ?? [])
const net = computed(() => toNumber(store.summary?.balance.net))
const hasIncome = computed(() => toNumber(store.summary?.income.household_actual) > 0)

async function handleSubmit() {
  error.value = ''
  submitting.value = true
  try {
    await store.setMyIncome({
      forecast_amount: String(forecastAmount.value || '0'),
      actual_amount: String(actualAmount.value || '0'),
    })
    editing.value = false
  } catch {
    error.value = 'Доход не сохранился. Попробуйте ещё раз.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="section" aria-labelledby="income-title">
    <div class="section-head">
      <h2 id="income-title">Доход</h2>
      <button v-if="!editing" class="btn btn-quiet" type="button" @click="editing = true">
        {{ myIncome ? 'Изменить мой' : 'Указать мой' }}
      </button>
    </div>

    <form v-if="editing" class="income-form" @submit.prevent="handleSubmit" @keydown.esc="editing = false">
      <label class="field">
        Ожидаю, ₽
        <input v-model="forecastAmount" type="number" inputmode="decimal" min="0" step="0.01" placeholder="0" />
      </label>
      <label class="field">
        Уже получил(а), ₽
        <input v-model="actualAmount" type="number" inputmode="decimal" min="0" step="0.01" placeholder="0" />
      </label>
      <div class="form-actions">
        <button class="btn btn-primary" type="submit" :disabled="submitting">Сохранить</button>
        <button class="btn btn-quiet" type="button" @click="editing = false">Отмена</button>
      </div>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    </form>

    <p v-if="perUser.length === 0 && !editing" class="empty">
      Доход за этот месяц ещё не указан. Каждый вносит свой, а итог считается на двоих.
    </p>

    <dl v-else-if="perUser.length > 0" class="people">
      <div v-for="entry in perUser" :key="entry.user_id" class="person">
        <dt>{{ entry.display_name }}</dt>
        <dd>
          <span class="num amount">{{ formatMoney(entry.actual) }}</span>
          <span class="num muted forecast">ожидается {{ formatMoney(entry.forecast) }}</span>
        </dd>
      </div>
      <div v-if="perUser.length > 1" class="person total">
        <dt>Вместе</dt>
        <dd>
          <span class="num amount">{{ formatMoney(store.summary?.income.household_actual) }}</span>
          <span class="num muted forecast">ожидается {{ formatMoney(store.summary?.income.household_forecast) }}</span>
        </dd>
      </div>
    </dl>

    <p v-if="hasIncome" class="balance" :class="{ negative: net < 0 }">
      <template v-if="net >= 0">
        После всех трат остаётся <strong class="num">{{ formatMoney(net) }}</strong>
      </template>
      <template v-else>
        Трат больше, чем дохода, на <strong class="num">{{ formatMoney(-net) }}</strong>
      </template>
    </p>
  </section>
</template>

<style scoped>
.section {
  gap: 0.75rem;
}

.income-form {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--ink-wash);
  border-radius: 10px;
}

.form-actions {
  display: flex;
  gap: 0.25rem;
}

.people {
  margin: 0;
  display: flex;
  flex-direction: column;
}

.person {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
  padding: 0.6rem 0;
  border-bottom: 1px solid var(--line);
}

.person dt {
  font-weight: 500;
}

.person dd {
  margin: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.amount {
  font-weight: 600;
}

.forecast {
  font-size: 0.8rem;
}

.total {
  border-bottom: none;
}

.total dt {
  font-weight: 600;
}

.balance {
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: var(--ink-wash);
  color: var(--text);
}

.balance strong {
  color: var(--ink);
}

.balance.negative {
  background: var(--red-wash);
}

.balance.negative strong {
  color: var(--red);
}
</style>
