<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMoneyStore } from '../stores/money'
import { formatMoney, plural, todayIso, toNumber } from '../utils/format'
import LoanItem from './LoanItem.vue'

// Bank loans: the total debt, what goes to the banks each month, and the list of loans.
const money = useMoneyStore()
const router = useRouter()

const totalDebt = computed(() => money.openLoans.reduce((sum, l) => sum + toNumber(l.balance), 0))
const monthly = computed(() =>
  money.openLoans.filter((l) => toNumber(l.balance) > 0).reduce((sum, l) => sum + toNumber(l.monthly_payment), 0),
)

const creating = ref(false)
const name = ref('')
const principal = ref('')
const startDate = ref(todayIso())
const rate = ref('')
const payment = ref('')
const paymentDay = ref('')
const error = ref('')

async function create() {
  error.value = ''
  try {
    const loan = await money.createLoan({
      name: name.value.trim(),
      principal: String(principal.value),
      start_date: startDate.value,
      rate_percent: String(rate.value || 0),
      monthly_payment: String(payment.value),
      payment_day: Number(paymentDay.value),
    })
    creating.value = false
    name.value = principal.value = rate.value = payment.value = paymentDay.value = ''
    startDate.value = todayIso()
    router.push({ name: 'money-loan', params: { loanId: loan.id } })
  } catch {
    error.value = 'Кредит не сохранился. Проверьте суммы, ставку и день платежа.'
  }
}
</script>

<template>
  <section class="section" aria-labelledby="loans-title">
    <div class="section-head">
      <h2 id="loans-title">Кредиты</h2>
      <button class="btn" type="button" :aria-expanded="creating" @click="creating = !creating">Новый кредит</button>
    </div>
    <p v-if="money.openLoans.length" class="total">
      Всего долг <strong class="num">{{ formatMoney(totalDebt) }}</strong>, платежи
      <strong class="num">{{ formatMoney(monthly) }}</strong> в месяц
    </p>

    <form v-if="creating" class="inline-form" @submit.prevent="create" @keydown.esc="creating = false">
      <label class="field">
        Название
        <input
          v-model="name"
          type="text"
          maxlength="100"
          required
          placeholder="Ипотека, автокредит, рассрочка на телефон"
          autofocus
        />
      </label>
      <div class="form-grid">
        <label class="field">
          Остаток долга, ₽
          <input v-model="principal" type="number" inputmode="decimal" min="0.01" step="0.01" required />
        </label>
        <label class="field">
          На дату
          <input v-model="startDate" type="date" required />
        </label>
        <label class="field">
          Ставка, % годовых
          <input v-model="rate" type="number" inputmode="decimal" min="0" max="99.999" step="0.001" placeholder="0" />
        </label>
        <label class="field">
          Ежемесячный платеж, ₽
          <input v-model="payment" type="number" inputmode="decimal" min="0.01" step="0.01" required />
        </label>
        <label class="field">
          День платежа
          <input v-model="paymentDay" type="number" inputmode="numeric" min="1" max="31" step="1" required />
        </label>
      </div>
      <p class="muted hint">
        Остаток возьмите из приложения банка. Платежи после этой даты записываются здесь и уходят из бюджета месяца.
      </p>
      <div class="form-actions">
        <button class="btn btn-primary" type="submit">Добавить кредит</button>
        <button class="btn btn-quiet" type="button" @click="creating = false">Отмена</button>
      </div>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    </form>

    <p v-if="!money.loans.length && !creating" class="empty">
      Добавьте ипотеку, автокредит или рассрочку: здесь будет видно, сколько осталось платить, когда следующий
      платеж и когда кредит закроется. Платежи уходят из бюджета месяца отдельной строкой.
    </p>

    <ul v-if="money.openLoans.length" class="loans">
      <LoanItem v-for="loan in money.openLoans" :key="loan.id" :loan="loan" />
    </ul>

    <details v-if="money.closedLoans.length" class="closed">
      <summary>
        {{ money.closedLoans.length }} {{ plural(money.closedLoans.length, 'закрытый кредит', 'закрытых кредита', 'закрытых кредитов') }}
      </summary>
      <ul class="loans">
        <LoanItem v-for="loan in money.closedLoans" :key="loan.id" :loan="loan" />
      </ul>
    </details>
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

.hint {
  font-size: 0.875rem;
}

.form-actions {
  display: flex;
  gap: 0.25rem;
}

.loans {
  list-style: none;
  margin: 0;
  padding: 0;
}

.closed {
  margin-top: 0.5rem;
}

.closed summary {
  width: fit-content;
  color: var(--muted);
  font-size: 0.9rem;
  cursor: pointer;
}

.closed summary:hover {
  color: var(--ink);
}

.closed[open] summary {
  margin-bottom: 0.5rem;
}
</style>
