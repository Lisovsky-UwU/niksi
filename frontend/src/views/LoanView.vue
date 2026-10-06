<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import ConfirmButton from '../components/ConfirmButton.vue'
import GoalCells from '../components/GoalCells.vue'
import { useBudgetStore } from '../stores/budget'
import { useMoneyStore } from '../stores/money'
import type { LoanPayment, LoanPaymentKind } from '../types/models'
import {
  MONTH_NAMES,
  formatAmount,
  formatLongDate,
  formatMoney,
  formatShortDate,
  formatSignedMoney,
  monthIn,
  plural,
  todayIso,
  toNumber,
} from '../utils/format'
import { PAYMENT_LABELS, dueState, formatRate, paidShare, suggestedPayment } from '../utils/loans'

// One loan: the debt on a notebook sheet, the next payment and the forecast, recording payments, and history.
const props = defineProps<{ loanId: string }>()
const money = useMoneyStore()
const budget = useBudgetStore()
const router = useRouter()

const loan = computed(() => money.loans.find((l) => l.id === Number(props.loanId)) ?? null)
const payments = computed(() => (loan.value ? money.loanPayments[loan.value.id] ?? [] : []))
const share = computed(() => (loan.value ? paidShare(loan.value) : 0))
const paidOff = computed(() => (loan.value ? toNumber(loan.value.balance) <= 0 : false))
const due = computed(() => (loan.value?.next_payment_date ? dueState(loan.value.next_payment_date) : null))

async function loadHistory() {
  if (loan.value) await money.loadLoanPayments(loan.value.id)
}
onMounted(loadHistory)
watch(() => props.loanId, loadHistory)

// --- recording a payment ---
const kind = ref<LoanPaymentKind>('regular')
const amount = ref('')
const paymentDate = ref(todayIso())
const note = ref('')
const paymentError = ref('')
const paymentDone = ref('')
const submitting = ref(false)

const KINDS: { value: LoanPaymentKind; label: string; button: string; hint: string }[] = [
  {
    value: 'regular',
    label: 'Платеж',
    button: 'Записать платеж',
    hint: 'Ежемесячный платеж: часть уйдет на проценты, остальное в счет долга. Деньги уйдут из бюджета месяца.',
  },
  {
    value: 'early',
    label: 'Досрочно',
    button: 'Погасить досрочно',
    hint: 'Вся сумма пойдет в счет долга. Деньги уйдут из бюджета месяца.',
  },
  {
    value: 'correction',
    label: 'Поправить остаток',
    button: 'Поправить остаток',
    hint: 'Если остаток в приложении банка другой, введите его. Бюджет месяца не изменится.',
  },
]
const currentKind = computed(() => KINDS.find((k) => k.value === kind.value) ?? KINDS[0])

// The regular payment is usually the same every month, so it is filled in.
function prefill() {
  if (!loan.value) return
  amount.value = kind.value === 'regular' ? String(suggestedPayment(loan.value)) : ''
}
watch(kind, () => {
  paymentError.value = ''
  paymentDone.value = ''
  prefill()
})
watch(loan, (now, before) => {
  if (now && !before) prefill()
}, { immediate: true })

async function submitPayment() {
  if (!loan.value || amount.value === '') return
  submitting.value = true
  paymentError.value = ''
  paymentDone.value = ''
  const isCorrection = kind.value === 'correction'
  try {
    const payment = await money.addLoanPayment(loan.value.id, {
      kind: kind.value,
      amount: isCorrection ? null : String(amount.value),
      new_balance: isCorrection ? String(amount.value) : null,
      payment_date: paymentDate.value,
      note: note.value.trim() || null,
    })
    paymentDone.value = isCorrection
      ? `Остаток теперь ${formatMoney(loan.value.balance)}.`
      : `Записано ${formatMoney(payment.amount)}, из них ${formatMoney(payment.principal_part)} в счет долга.`
    note.value = ''
    prefill()
    // A payment changes the open month's balance too.
    await budget.refreshSummary()
  } catch {
    paymentError.value = isCorrection
      ? 'Остаток не сохранился. Проверьте сумму.'
      : 'Платеж не записан: сумма больше долга с процентами. Проверьте сумму.'
  } finally {
    submitting.value = false
  }
}

// --- history, grouped by month ---
const historyError = ref('')
const months = computed(() => {
  const groups: { key: string; label: string; paid: number; items: LoanPayment[] }[] = []
  for (const p of payments.value) {
    const key = p.payment_date.slice(0, 7)
    let group = groups[groups.length - 1]
    if (!group || group.key !== key) {
      const [y, m] = key.split('-').map(Number)
      group = { key, label: `${MONTH_NAMES[m - 1]} ${y}`, paid: 0, items: [] }
      groups.push(group)
    }
    group.items.push(p)
    group.paid += toNumber(p.amount)
  }
  return groups
})

function paymentMeta(p: LoanPayment): string {
  if (p.kind === 'regular') {
    return `${formatMoney(p.principal_part)} в счет долга, ${formatMoney(p.interest_part)} проценты`
  }
  if (p.kind === 'correction') {
    const change = -toNumber(p.principal_part)
    return `остаток ${change > 0 ? 'вырос' : 'уменьшился'} на ${formatMoney(Math.abs(change))}`
  }
  return ''
}

async function removePayment(paymentId: number) {
  if (!loan.value) return
  historyError.value = ''
  try {
    await money.deleteLoanPayment(loan.value.id, paymentId)
    await budget.refreshSummary()
  } catch {
    historyError.value = 'Запись не удалилась. Обновите страницу и попробуйте еще раз.'
  }
}

// --- the loan itself ---
const editing = ref(false)
const editName = ref('')
const editPrincipal = ref('')
const editStart = ref('')
const editRate = ref('')
const editPayment = ref('')
const editDay = ref('')
const loanError = ref('')

function startEditing() {
  if (!loan.value) return
  editName.value = loan.value.name
  editPrincipal.value = String(toNumber(loan.value.principal))
  editStart.value = loan.value.start_date
  editRate.value = String(toNumber(loan.value.rate_percent))
  editPayment.value = String(toNumber(loan.value.monthly_payment))
  editDay.value = String(loan.value.payment_day)
  loanError.value = ''
  editing.value = true
}

async function saveLoan(close: boolean) {
  if (!loan.value) return
  loanError.value = ''
  const l = loan.value
  const useForm = editing.value
  try {
    await money.updateLoan(l.id, {
      name: useForm ? editName.value.trim() || l.name : l.name,
      principal: useForm ? String(editPrincipal.value) : l.principal,
      start_date: useForm ? editStart.value : l.start_date,
      rate_percent: useForm ? String(editRate.value || 0) : l.rate_percent,
      monthly_payment: useForm ? String(editPayment.value) : l.monthly_payment,
      payment_day: useForm ? Number(editDay.value) : l.payment_day,
      is_closed: close,
    })
    editing.value = false
  } catch {
    loanError.value = 'Не сохранилось. Проверьте суммы, ставку и день платежа.'
  }
}

async function removeLoan() {
  if (!loan.value) return
  loanError.value = ''
  try {
    await money.deleteLoan(loan.value.id)
    router.push({ name: 'money-loans' })
  } catch {
    loanError.value = 'По кредиту уже есть платежи, поэтому его можно только закрыть.'
  }
}
</script>

<template>
  <div v-if="loan" class="loan-page">
    <RouterLink :to="{ name: 'money-loans' }" class="back">
      <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3 5 8l5 5" /></svg>
      Кредиты
    </RouterLink>

    <section class="notebook-sheet grid-paper" aria-labelledby="loan-name">
      <div class="sheet-body">
        <div class="figures">
          <p class="kind">Остаток долга<template v-if="loan.is_closed">, кредит закрыт</template></p>
          <h1 id="loan-name" class="loan-name">{{ loan.name }}</h1>
          <p :key="loan.balance" class="hand hand-figure num">
            {{ formatAmount(loan.balance) }}<span class="currency">₽</span>
          </p>

          <GoalCells size="lg" :share="share" :label="`Выплачено ${Math.floor(share * 100)}% долга`" />
          <p class="context">
            Выплачено <strong class="num">{{ formatMoney(toNumber(loan.principal) - toNumber(loan.balance)) }}</strong>
            из <span class="num">{{ formatMoney(loan.principal) }}</span> с {{ formatLongDate(loan.start_date) }}.
          </p>

          <dl class="terms">
            <div>
              <dt>Ставка</dt>
              <dd class="num">{{ formatRate(loan.rate_percent) }} годовых</dd>
            </div>
            <div>
              <dt>Платеж</dt>
              <dd class="num">{{ formatMoney(loan.monthly_payment) }}, {{ loan.payment_day }}-го числа</dd>
            </div>
            <div v-if="loan.next_payment_date">
              <dt>Следующий</dt>
              <dd :class="`due-${due}`">
                {{ formatLongDate(loan.next_payment_date) }}<template v-if="due === 'overdue'">, просрочен</template>
                <template v-else-if="due === 'today'">, сегодня</template>
              </dd>
            </div>
          </dl>

          <p v-if="!loan.is_closed && !paidOff" class="context forecast">
            <template v-if="loan.payoff_date && loan.payments_left">
              При таком платеже кредит закроется в {{ monthIn(Number(loan.payoff_date.slice(5, 7))) }}
              {{ loan.payoff_date.slice(0, 4) }}: еще {{ loan.payments_left }}
              {{ plural(loan.payments_left, 'платеж', 'платежа', 'платежей') }}, из них примерно
              <strong class="num">{{ formatMoney(Math.round(toNumber(loan.interest_left))) }}</strong> уйдет на проценты.
            </template>
            <template v-else>
              Платеж не покрывает проценты, и долг не уменьшается. Проверьте ставку и сумму платежа.
            </template>
          </p>
        </div>

        <div v-if="loan.is_closed" class="panel">
          <p>Кредит закрыт: история платежей сохранена, новые не записываются.</p>
          <button class="btn btn-primary" type="button" @click="saveLoan(false)">Вернуть в текущие</button>
        </div>

        <div v-else-if="paidOff" class="panel">
          <p>Долг выплачен полностью. Закройте кредит, чтобы он ушел из текущих.</p>
          <button class="btn btn-primary" type="button" @click="saveLoan(true)">Закрыть кредит</button>
        </div>

        <form v-else class="panel" @submit.prevent="submitPayment">
          <fieldset class="kinds">
            <legend class="visually-hidden">Что записать</legend>
            <label v-for="k in KINDS" :key="k.value" class="chip">
              <input v-model="kind" type="radio" name="loan-payment-kind" :value="k.value" />
              <span>{{ k.label }}</span>
            </label>
          </fieldset>
          <p class="muted hint">{{ currentKind.hint }}</p>
          <label class="amount-field">
            <span class="visually-hidden">
              {{ kind === 'correction' ? 'Остаток по данным банка, рублей' : 'Сумма в рублях' }}
            </span>
            <input
              v-model="amount"
              type="number"
              inputmode="decimal"
              :min="kind === 'correction' ? 0 : 0.01"
              step="0.01"
              :placeholder="kind === 'correction' ? 'Остаток по банку' : '0'"
              required
            />
            <span class="amount-currency" aria-hidden="true">₽</span>
          </label>
          <div class="form-grid">
            <label class="field">
              Дата
              <input v-model="paymentDate" type="date" required />
            </label>
            <label class="field">
              Комментарий
              <input v-model="note" type="text" maxlength="200" placeholder="Необязательно" />
            </label>
          </div>
          <button class="btn btn-primary submit" type="submit" :disabled="submitting || amount === ''">
            {{ currentKind.button }}
          </button>
          <p v-if="paymentError" class="error-text" role="alert">{{ paymentError }}</p>
          <p v-else-if="paymentDone" class="done" role="status">{{ paymentDone }}</p>
        </form>
      </div>
    </section>

    <section class="section" aria-labelledby="history-title">
      <div class="section-head">
        <h2 id="history-title">Платежи</h2>
        <span v-if="payments.length" class="muted">
          {{ payments.length }} {{ plural(payments.length, 'запись', 'записи', 'записей') }}
        </span>
      </div>
      <p v-if="historyError" class="error-text" role="alert">{{ historyError }}</p>
      <p v-if="!payments.length" class="empty">Платежей пока не было.</p>
      <div v-for="month in months" :key="month.key" class="month">
        <h3 class="month-head">
          <span>{{ month.label }}</span>
          <span v-if="month.paid" class="num muted">{{ formatMoney(month.paid) }}</span>
        </h3>
        <ul class="payments">
          <li v-for="p in month.items" :key="p.id" class="payment">
            <span class="what">
              <span class="title">{{ PAYMENT_LABELS[p.kind] }}</span>
              <span class="meta">
                {{ formatShortDate(p.payment_date) }}<template v-if="paymentMeta(p)">, {{ paymentMeta(p) }}</template>
                <template v-if="p.note">, {{ p.note }}</template>
              </span>
            </span>
            <span class="num amount" :class="`is-${p.kind}`">
              <template v-if="p.kind === 'correction'">{{ formatSignedMoney(-toNumber(p.principal_part)) }}</template>
              <template v-else>−{{ formatMoney(p.amount) }}</template>
            </span>
            <ConfirmButton icon class="remove" confirm-label="Удалить запись" @confirm="removePayment(p.id)" />
          </li>
        </ul>
      </div>
    </section>

    <section class="section" aria-labelledby="loan-settings-title">
      <div class="section-head">
        <h2 id="loan-settings-title">Условия кредита</h2>
      </div>
      <form v-if="editing" class="edit-form" @submit.prevent="saveLoan(loan.is_closed)" @keydown.esc="editing = false">
        <label class="field">
          Название
          <input v-model="editName" type="text" maxlength="100" required autofocus />
        </label>
        <div class="form-grid">
          <label class="field">
            Остаток долга, ₽
            <input v-model="editPrincipal" type="number" inputmode="decimal" min="0.01" step="0.01" required />
          </label>
          <label class="field">
            На дату
            <input v-model="editStart" type="date" required />
          </label>
          <label class="field">
            Ставка, % годовых
            <input v-model="editRate" type="number" inputmode="decimal" min="0" max="99.999" step="0.001" />
          </label>
          <label class="field">
            Ежемесячный платеж, ₽
            <input v-model="editPayment" type="number" inputmode="decimal" min="0.01" step="0.01" required />
          </label>
          <label class="field">
            День платежа
            <input v-model="editDay" type="number" inputmode="numeric" min="1" max="31" step="1" required />
          </label>
        </div>
        <p class="muted hint">
          Остаток и дата - это долг на момент, когда кредит добавили сюда. Уже записанные платежи не пересчитываются.
        </p>
        <div class="form-actions">
          <button class="btn btn-primary" type="submit">Сохранить</button>
          <button class="btn btn-quiet" type="button" @click="editing = false">Отмена</button>
        </div>
      </form>
      <div v-else class="loan-actions">
        <button class="btn" type="button" @click="startEditing">Изменить условия</button>
        <button v-if="!loan.is_closed" class="btn btn-quiet" type="button" @click="saveLoan(true)">Закрыть кредит</button>
        <ConfirmButton v-if="!payments.length" confirm-label="Удалить кредит" @confirm="removeLoan" />
      </div>
      <p v-if="loanError" class="error-text" role="alert">{{ loanError }}</p>
    </section>
  </div>

  <div v-else class="missing">
    <p>Такого кредита нет. Возможно, его удалили.</p>
    <RouterLink :to="{ name: 'money-loans' }">К кредитам</RouterLink>
  </div>
</template>

<style scoped>
.loan-page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.loan-page > .section {
  max-width: 46rem;
}

.back {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  align-self: flex-start;
  margin-left: -0.35rem;
  padding: 0.25rem 0.5rem 0.25rem 0.35rem;
  border-radius: var(--radius-control);
  color: var(--muted);
  font-weight: 500;
  text-decoration: none;
}

.back:hover {
  color: var(--ink);
  background: var(--ink-wash);
}

.back svg {
  width: 1rem;
  height: 1rem;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.sheet-body {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  gap: 2rem 3rem;
  align-items: start;
  padding-top: 1rem;
}

.figures {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  min-width: 0;
}

.kind {
  color: var(--muted);
  font-weight: 500;
}

.loan-name {
  font-size: 1.6rem;
  overflow-wrap: anywhere;
}

.context {
  max-width: 30rem;
  color: var(--muted);
}

.context strong {
  color: var(--text);
  font-weight: 600;
}

/* Terms written in the margin of the sheet: a label on the left, the figure on the right. */
.terms {
  display: grid;
  gap: 0.2rem;
  margin: 0.4rem 0 0;
  max-width: 30rem;
}

.terms div {
  display: grid;
  grid-template-columns: 7rem minmax(0, 1fr);
  gap: 0.75rem;
  padding: 0.3rem 0;
  border-bottom: 1px dashed var(--line);
}

.terms dt {
  color: var(--muted);
}

.terms dd {
  margin: 0;
  font-weight: 500;
}

.due-overdue {
  color: var(--red);
}

.due-today,
.due-soon {
  color: var(--loan);
}

.forecast {
  padding-left: 0.75rem;
  border-left: 3px solid color-mix(in srgb, var(--loan) 55%, transparent);
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.25rem;
  background: var(--sheet);
  border: 1px solid var(--line);
  border-radius: 12px;
}

.kinds {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0;
  padding: 0;
  border: none;
}

.hint {
  font-size: 0.875rem;
}

.amount-field {
  position: relative;
  display: block;
}

.amount-field input {
  font-size: 2rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  padding: 0.35rem 2.5rem 0.35rem 0.75rem;
  min-height: 3.5rem;
  appearance: textfield;
  -moz-appearance: textfield;
}

.amount-field input::placeholder {
  font-size: 1.1rem;
  font-weight: 400;
}

.amount-field input::-webkit-outer-spin-button,
.amount-field input::-webkit-inner-spin-button {
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

.submit {
  align-self: flex-start;
}

.done {
  color: var(--ink);
  font-size: 0.95rem;
}

.month {
  padding-top: 0.5rem;
}

.month-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 0.95rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--line);
}

.month-head .muted {
  font-weight: 500;
}

.payments {
  list-style: none;
  margin: 0;
  padding: 0;
}

.payment {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto 2rem;
  align-items: center;
  column-gap: 0.75rem;
  padding: 0.5rem 0;
  border-bottom: 1px dashed var(--line);
}

.payment:last-child {
  border-bottom: none;
}

.payment .amount {
  font-weight: 600;
  font-size: 1rem;
}

.amount.is-regular,
.amount.is-early {
  color: var(--loan);
}

.amount.is-correction {
  color: var(--muted);
}

.loan-actions,
.form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.edit-form {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--ink-wash);
  border-radius: 10px;
}

.missing {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 2rem 0;
}

@media (max-width: 860px) {
  .sheet-body {
    grid-template-columns: 1fr;
  }
}
</style>
