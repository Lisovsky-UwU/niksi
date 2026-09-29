<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useMoneyStore } from '../stores/money'
import type { SavingsPotKind } from '../types/models'
import { formatMoney, plural, toNumber } from '../utils/format'
import SavingsPotItem from './SavingsPotItem.vue'

// Current savings only; archived pots live on their own tab.
const money = useMoneyStore()

const accounts = computed(() => money.activePots.filter((p) => p.kind !== 'goal'))
const goals = computed(() => money.activePots.filter((p) => p.kind === 'goal'))
const total = computed(() => money.activePots.reduce((sum, p) => sum + toNumber(p.balance), 0))

const creating = ref(false)
const kind = ref<SavingsPotKind>('goal')
const name = ref('')
const targetAmount = ref('')
const targetDate = ref('')
const error = ref('')

const KIND_OPTIONS: { value: SavingsPotKind; label: string; placeholder: string }[] = [
  { value: 'goal', label: 'Цель', placeholder: 'Новый шкаф, машина, взнос по ипотеке' },
  { value: 'account', label: 'Накопительный счёт', placeholder: 'Накопительный в банке' },
  { value: 'deposit', label: 'Вклад', placeholder: 'Вклад на полгода' },
]
const placeholder = computed(() => KIND_OPTIONS.find((k) => k.value === kind.value)?.placeholder ?? '')

async function create() {
  error.value = ''
  try {
    await money.createPot({
      name: name.value.trim(),
      kind: kind.value,
      target_amount: targetAmount.value ? String(targetAmount.value) : null,
      target_date: targetDate.value || null,
    })
    creating.value = false
    name.value = ''
    targetAmount.value = ''
    targetDate.value = ''
  } catch {
    error.value = 'Копилка не создалась. Проверьте поля и попробуйте ещё раз.'
  }
}
</script>

<template>
  <section class="section" aria-labelledby="savings-title">
    <div class="section-head">
      <h2 id="savings-title">Накопления</h2>
      <button class="btn" type="button" :aria-expanded="creating" @click="creating = !creating">Новая копилка</button>
    </div>
    <p v-if="money.activePots.length" class="total">
      Всего отложено <strong class="num">{{ formatMoney(total) }}</strong>
    </p>

    <form v-if="creating" class="inline-form" @submit.prevent="create" @keydown.esc="creating = false">
      <fieldset class="kinds">
        <legend class="visually-hidden">Что это</legend>
        <label v-for="option in KIND_OPTIONS" :key="option.value" class="chip">
          <input v-model="kind" type="radio" name="pot-kind" :value="option.value" />
          <span>{{ option.label }}</span>
        </label>
      </fieldset>
      <label class="field">
        Название
        <input v-model="name" type="text" maxlength="100" required :placeholder="placeholder" autofocus />
      </label>
      <div class="form-grid">
        <label class="field">
          {{ kind === 'goal' ? 'Сколько нужно, ₽' : 'Цель, ₽ (необязательно)' }}
          <input
            v-model="targetAmount"
            type="number"
            inputmode="decimal"
            min="1"
            step="0.01"
            :required="kind === 'goal'"
          />
        </label>
        <label class="field">
          К какой дате (необязательно)
          <input v-model="targetDate" type="date" />
        </label>
      </div>
      <div class="form-actions">
        <button class="btn btn-primary" type="submit">Создать</button>
        <button class="btn btn-quiet" type="button" @click="creating = false">Отмена</button>
      </div>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    </form>

    <p v-if="!money.activePots.length && !creating" class="empty">
      Заведите копилку для накопительного счёта или вклада, или цель: шкаф, машину, первый взнос по ипотеке.
      Отложенные деньги уходят из бюджета месяца и копятся здесь.
    </p>

    <template v-if="goals.length">
      <h3 class="group-title">Цели</h3>
      <ul class="pots">
        <SavingsPotItem v-for="pot in goals" :key="pot.id" :pot="pot" />
      </ul>
    </template>

    <template v-if="accounts.length">
      <h3 class="group-title">Счета и вклады</h3>
      <ul class="pots">
        <SavingsPotItem v-for="pot in accounts" :key="pot.id" :pot="pot" />
      </ul>
    </template>

    <RouterLink v-if="money.archivedPots.length" :to="{ name: 'money-archive' }" class="archive-link">
      В архиве {{ money.archivedPots.length }}
      {{ plural(money.archivedPots.length, 'копилка', 'копилки', 'копилок') }}
    </RouterLink>
  </section>
</template>

<style scoped>
.section {
  gap: 0.75rem;
}

.total {
  color: var(--muted);
}

.total strong {
  color: var(--text);
  font-weight: 600;
}

.inline-form {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--ink-wash);
  border-radius: 10px;
}

.kinds {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0;
  padding: 0;
  border: none;
}

.form-actions {
  display: flex;
  gap: 0.25rem;
}

.group-title {
  margin-top: 0.75rem;
  font-size: 1rem;
  color: var(--muted);
  font-weight: 500;
}

.pots {
  list-style: none;
  margin: 0;
  padding: 0;
}

.archive-link {
  align-self: flex-start;
  margin-top: 0.5rem;
  color: var(--muted);
  font-size: 0.9rem;
}

.archive-link:hover {
  color: var(--ink);
}
</style>
