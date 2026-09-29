<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useBudgetStore } from '../stores/budget'
import { useMoneyStore } from '../stores/money'
import { formatMoney, formatSignedMoney, monthOf, toNumber } from '../utils/format'

const store = useBudgetStore()
const money = useMoneyStore()

const summary = computed(() => store.summary)
const balance = computed(() => summary.value?.balance)
const carryover = computed(() => summary.value?.carryover)

type Kind = 'income' | 'expenses' | 'grey' | 'savings' | 'adjust'

// Where the month's money went, in the order it flows. Each kind has its own colour.
// The reconciliation tile only appears when there was a difference.
const tiles = computed(() => {
  const b = balance.value
  if (!b) return []
  const savings = toNumber(b.savings_net)
  const adjust = toNumber(b.adjustments)
  const rows: { kind: Kind; label: string; value: number }[] = [
    { kind: 'income', label: 'Доходы', value: toNumber(b.income_actual) },
    { kind: 'expenses', label: 'Траты', value: -toNumber(b.total_spent) },
    { kind: 'grey', label: 'Серая зона', value: -toNumber(b.grey_zone_taken) },
    { kind: 'savings', label: savings >= 0 ? 'В накопления' : 'Из накоплений', value: -savings },
  ]
  if (adjust !== 0) rows.push({ kind: 'adjust', label: 'Расхождение сверки', value: adjust })
  return rows
})

// The sign written in the margin of the column sum. A zero outflow still reads as "−".
function op(kind: Kind, value: number): string {
  if (value > 0) return '+'
  if (value < 0) return '−'
  return kind === 'income' ? '+' : '−'
}

const closing = computed(() => toNumber(carryover.value?.closing))

// --- carry-over editing ---
const editing = ref(false)
const carryAmount = ref('')
const error = ref('')

watch(editing, (open) => {
  if (open) carryAmount.value = String(toNumber(carryover.value?.carried_over))
})

async function saveCarryover() {
  error.value = ''
  try {
    await store.setCarryover(String(carryAmount.value || '0'))
    editing.value = false
  } catch {
    error.value = 'Не сохранилось. Попробуйте ещё раз.'
  }
}

async function resetCarryover() {
  await store.setCarryover(null)
  editing.value = false
}

// --- expected money on hand, from the last reconciliation ---
onMounted(() => money.refreshBalance().catch(() => undefined))
watch(summary, () => money.refreshBalance().catch(() => undefined))
</script>

<template>
  <section v-if="summary && balance && carryover" class="section" aria-labelledby="balance-title">
    <div class="section-head">
      <h2 id="balance-title">Итог месяца</h2>
    </div>

    <!-- A column sum on ruled lines: each kind of money is marked with its own highlighter. -->
    <div class="ledger">
      <div class="line is-carry">
        <span class="op" aria-hidden="true" />
        <span class="label">
          С прошлого месяца
          <span v-if="carryover.is_manual" class="tag">задано вручную</span>
        </span>
        <span class="amount num">{{ formatMoney(carryover.carried_over) }}</span>
      </div>
      <div v-for="tile in tiles" :key="tile.kind" class="line" :class="`is-${tile.kind}`">
        <span class="op" aria-hidden="true">{{ op(tile.kind, tile.value) }}</span>
        <span class="label"><span class="marker">{{ tile.label }}</span></span>
        <span class="amount num" :aria-label="formatSignedMoney(tile.value)">{{ formatMoney(Math.abs(tile.value)) }}</span>
      </div>
    </div>

    <div class="total" :class="{ negative: closing < 0 }">
      <span class="total-label">Остаток на конец {{ monthOf(summary.month.month) }}</span>
      <span class="total-value hand num">{{ formatMoney(closing) }}</span>
      <span class="note">Переходит в следующий месяц.</span>
    </div>

    <div class="carry-actions">
      <button v-if="!editing" class="btn btn-quiet" type="button" @click="editing = true">
        Поправить перенос с прошлого месяца
      </button>
      <form v-else class="inline-form" @submit.prevent="saveCarryover" @keydown.esc="editing = false">
        <label class="field">
          С прошлого месяца осталось, ₽
          <input v-model="carryAmount" type="number" inputmode="decimal" step="0.01" required autofocus />
        </label>
        <p class="muted small-text">
          Пригодится для первого месяца или если с прошлого месяца на самом деле осталось другое.
        </p>
        <div class="form-actions">
          <button class="btn btn-primary" type="submit">Сохранить</button>
          <button v-if="carryover.is_manual" class="btn btn-quiet" type="button" @click="resetCarryover">
            Считать автоматически
          </button>
          <button class="btn btn-quiet" type="button" @click="editing = false">Отмена</button>
        </div>
        <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      </form>
    </div>

    <RouterLink v-if="money.balance" to="/money" class="on-hand">
      <template v-if="money.balance.expected_now !== null">
        <span>По записям сейчас на руках</span>
        <strong class="num">{{ formatMoney(money.balance.expected_now) }}</strong>
        <span class="link-text">Сверить с реальностью</span>
      </template>
      <template v-else>
        <span>Сверьте, сколько денег у вас на самом деле, и Niksi будет ловить неучтённые траты.</span>
        <span class="link-text">Первая сверка</span>
      </template>
    </RouterLink>
  </section>
</template>

<style scoped>
.section {
  gap: 0.75rem;
}

/* Ruled lines of the notebook: sign in the margin, what, how much. */
.ledger {
  display: flex;
  flex-direction: column;
}

.line {
  --tone: var(--text);
  display: grid;
  grid-template-columns: 1.1rem minmax(0, 1fr) auto;
  align-items: baseline;
  column-gap: 0.6rem;
  padding: 0.6rem 0;
  border-bottom: 1px solid var(--grid);
}

.is-income {
  --tone: var(--ink);
}

.is-expenses {
  --tone: var(--red);
}

.is-grey {
  --tone: var(--grey-zone);
}

.is-savings {
  --tone: var(--green);
}

.is-adjust {
  --tone: var(--amber);
}

.op {
  color: var(--tone);
  font-size: 1.15rem;
  font-weight: 600;
  line-height: 1;
  text-align: center;
}

.label {
  min-width: 0;
  font-weight: 500;
}

/* Highlighter swipe over the lower half of the word, in the kind's own colour. */
.marker {
  padding: 0 0.15em;
  margin: 0 -0.15em;
  background: linear-gradient(
    transparent 38%,
    color-mix(in srgb, var(--tone) var(--marker-strength), transparent) 38%,
    color-mix(in srgb, var(--tone) var(--marker-strength), transparent) 94%,
    transparent 94%
  );
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
}

.amount {
  color: var(--tone);
  font-size: 1.1rem;
  font-weight: 600;
  text-align: right;
}

.is-carry .label {
  color: var(--muted);
  font-weight: 400;
}

.is-carry .amount {
  font-size: 1rem;
}

.tag {
  display: block;
  font-size: 0.8rem;
  font-style: italic;
  color: var(--muted);
}

/* The result sits under a double rule, like a total in an account book. */
.total {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 0 1rem;
  margin-top: 0.15rem;
  padding-top: 0.6rem;
  border-top: 4px double var(--text);
}

.total-label {
  font-weight: 600;
}

.total-value {
  margin-left: auto;
  font-size: 2.6rem;
}

.total.negative .total-value {
  color: var(--red);
}

.note {
  flex-basis: 100%;
  font-size: 0.85rem;
  color: var(--muted);
}

.carry-actions .btn-quiet {
  margin-left: -0.5rem;
  font-size: 0.9rem;
}

.inline-form {
  display: grid;
  gap: 0.6rem;
  padding: 1rem;
  background: var(--ink-wash);
  border-radius: 10px;
}

.small-text {
  font-size: 0.85rem;
}

.form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.on-hand {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.25rem 0.5rem;
  padding: 0.85rem 1rem;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--sheet);
  color: var(--text);
  text-decoration: none;
  transition: border-color 0.15s;
}

.on-hand:hover {
  border-color: var(--ink);
}

.on-hand strong {
  color: var(--ink);
}

.link-text {
  flex-basis: 100%;
  color: var(--ink);
  font-size: 0.9rem;
  font-weight: 500;
}
</style>
