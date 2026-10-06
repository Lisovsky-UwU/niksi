<script setup lang="ts">
import { computed, ref } from 'vue'
import ConfirmButton from '../components/ConfirmButton.vue'
import { useMoneyStore } from '../stores/money'
import type { Reconciliation } from '../types/models'
import { formatAmount, formatLongDate, formatMoney, formatSignedMoney, formatShortDate, todayIso, toNumber } from '../utils/format'

const money = useMoneyStore()
const last = computed(() => money.balance?.last_reconciliation ?? null)
const expected = computed(() => money.balance?.expected_now ?? null)

// What moved since the last reconciliation, in the order it affects the money on hand.
const flows = computed(() => {
  const f = money.balance?.flows_since
  if (!f) return []
  return [
    { label: 'Доходы', value: toNumber(f.income) },
    { label: 'Траты', value: -toNumber(f.expenses) },
    { label: 'Серая зона', value: -toNumber(f.grey_zone) },
    { label: 'В накопления', value: -toNumber(f.savings_in) },
    { label: 'Из накоплений', value: toNumber(f.savings_out) },
    { label: 'Кредиты', value: -toNumber(f.loan_payments) },
  ].filter((row) => row.value !== 0)
})

// --- reconcile form ---
const actual = ref('')
const balanceDate = ref(todayIso())
const note = ref('')
const submitting = ref(false)
const error = ref('')
const result = ref<Reconciliation | null>(null)

async function reconcile() {
  if (actual.value === '') return
  error.value = ''
  submitting.value = true
  try {
    result.value = await money.reconcile({
      actual_balance: String(actual.value),
      balance_date: balanceDate.value,
      note: note.value.trim() || null,
    })
    actual.value = ''
    note.value = ''
  } catch {
    error.value = last.value
      ? `Сверка не сохранилась. Дата не может быть раньше прошлой сверки (${formatLongDate(last.value.balance_date)}).`
      : 'Сверка не сохранилась. Попробуйте ещё раз.'
  } finally {
    submitting.value = false
  }
}

async function undo(id: number) {
  await money.undoReconciliation(id)
  if (result.value?.id === id) result.value = null
}
</script>

<template>
  <div class="money">
      <section class="notebook-sheet grid-paper" aria-labelledby="money-headline">
        <div class="sheet-body">
          <div class="figures">
            <template v-if="expected !== null && last">
              <h1 id="money-headline" class="headline">По записям сейчас на руках</h1>
              <p :key="expected" class="hand hand-figure num" :class="{ negative: toNumber(expected) < 0 }">
                {{ formatAmount(expected) }}<span class="currency">₽</span>
              </p>
              <p class="context">
                Последняя сверка {{ formatLongDate(last.balance_date) }}:
                <strong class="num">{{ formatMoney(last.actual_balance) }}</strong>.
                <template v-if="flows.length">С тех пор:</template>
                <template v-else>С тех пор ничего не записано.</template>
              </p>
              <dl v-if="flows.length" class="flows">
                <div v-for="row in flows" :key="row.label" class="flow">
                  <dt>{{ row.label }}</dt>
                  <dd class="num" :class="{ minus: row.value < 0 }">{{ formatSignedMoney(row.value) }}</dd>
                </div>
              </dl>
            </template>
            <template v-else>
              <h1 id="money-headline" class="headline">Сверок ещё не было</h1>
              <p class="intro">
                Посчитайте, сколько общих денег у вас сейчас на картах и наличными, и запишите справа.
                Это станет точкой отсчёта: дальше Niksi будет знать, сколько денег должно быть, и покажет,
                если по факту их больше или меньше.
              </p>
            </template>
          </div>

          <form class="reconcile" @submit.prevent="reconcile">
            <h2 class="form-title">Сколько денег на самом деле?</h2>
            <p class="muted hint">Все общие деньги: карты и наличные. Накопления и вклады сюда не входят.</p>
            <label class="amount">
              <span class="visually-hidden">Сумма в рублях</span>
              <input v-model="actual" type="number" inputmode="decimal" step="0.01" placeholder="0" required />
              <span class="amount-currency" aria-hidden="true">₽</span>
            </label>
            <div class="form-grid">
              <label class="field">
                На дату
                <input v-model="balanceDate" type="date" required />
              </label>
              <label class="field">
                Комментарий
                <input v-model="note" type="text" maxlength="200" placeholder="Например, карты и наличные" />
              </label>
            </div>
            <button class="btn btn-primary submit" type="submit" :disabled="submitting || actual === ''">
              {{ last ? 'Сверить' : 'Записать точку отсчёта' }}
            </button>
            <p v-if="error" class="error-text" role="alert">{{ error }}</p>
            <p v-else-if="result" class="result" role="status">
              <template v-if="result.expected_balance === null">Точка отсчёта записана.</template>
              <template v-else-if="toNumber(result.difference) === 0">Всё сошлось до рубля.</template>
              <template v-else>
                Расхождение <strong class="num">{{ formatSignedMoney(result.difference) }}</strong>.
                {{ toNumber(result.difference) < 0 ? 'Похоже, что-то не записали.' : 'Денег больше, чем по записям.' }}
                Разница учтена в месяце, дальше считаем от {{ formatMoney(result.actual_balance) }}.
              </template>
            </p>
          </form>
        </div>
      </section>

      <section class="section" aria-labelledby="history-title">
          <div class="section-head">
            <h2 id="history-title">История сверок</h2>
          </div>
          <p v-if="!money.reconciliations.length" class="empty">Здесь появятся все сверки и расхождения.</p>
          <ul v-else class="history">
            <li v-for="(r, index) in money.reconciliations" :key="r.id" class="rec">
              <div class="rec-line">
                <span class="date">{{ formatShortDate(r.balance_date) }}</span>
                <span class="num">{{ formatMoney(r.actual_balance) }}</span>
              </div>
              <div class="rec-line sub">
                <span v-if="r.expected_balance === null" class="muted">точка отсчёта</span>
                <span v-else-if="toNumber(r.difference) === 0" class="muted">сошлось</span>
                <span v-else class="num diff" :class="{ minus: toNumber(r.difference) < 0 }">
                  {{ formatSignedMoney(r.difference) }}
                </span>
                <ConfirmButton v-if="index === 0" label="Отменить" confirm-label="Отменить сверку" @confirm="undo(r.id)" />
              </div>
              <p v-if="r.note" class="muted note">{{ r.note }}</p>
            </li>
          </ul>
      </section>
  </div>
</template>

<style scoped>
.money {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.money > .section {
  max-width: 46rem;
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
  gap: 0.75rem;
}

.headline {
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: 0;
}

.negative {
  color: var(--red);
}

.context,
.intro {
  max-width: 30rem;
  color: var(--muted);
}

.intro {
  color: var(--text);
  line-height: 1.6;
}

.context strong {
  color: var(--text);
  font-weight: 600;
}

.flows {
  margin: 0;
  max-width: 22rem;
}

.flow {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.2rem 0;
}

.flow dt {
  color: var(--muted);
}

.flow dd {
  margin: 0;
  font-weight: 500;
}

.reconcile {
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

.hint {
  font-size: 0.875rem;
  margin-top: -0.4rem;
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


.submit {
  align-self: flex-start;
}

.result {
  font-size: 0.95rem;
}

.result strong {
  color: var(--ink);
}

.history {
  list-style: none;
  margin: 0;
  padding: 0;
}

.rec {
  padding: 0.7rem 0;
  border-bottom: 1px solid var(--line);
}

.rec-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.rec-line .num {
  font-weight: 600;
}

.date {
  font-weight: 500;
}

.sub {
  min-height: 2rem;
  font-size: 0.9rem;
}

.diff {
  color: var(--ink);
}

.minus {
  color: var(--red);
}

.note {
  font-size: 0.85rem;
}

@media (max-width: 860px) {
  .sheet-body {
    grid-template-columns: 1fr;
  }
}

</style>
