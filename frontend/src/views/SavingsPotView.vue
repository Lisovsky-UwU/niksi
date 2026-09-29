<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import ConfirmButton from '../components/ConfirmButton.vue'
import GoalCells from '../components/GoalCells.vue'
import { useBudgetStore } from '../stores/budget'
import { useMoneyStore } from '../stores/money'
import type { SavingsTransfer, SavingsTransferDirection } from '../types/models'
import {
  MONTH_NAMES,
  formatAmount,
  formatLongDate,
  formatMoney,
  formatShortDate,
  formatSignedMoney,
  plural,
  todayIso,
  toNumber,
} from '../utils/format'
import { DIRECTION_LABELS, KIND_LABELS, goalStats } from '../utils/savings'

// One savings pot: its balance on a notebook sheet, what can be done with it, and its history.
const props = defineProps<{ potId: string }>()
const money = useMoneyStore()
const budget = useBudgetStore()
const router = useRouter()

const pot = computed(() => money.pots.find((p) => p.id === Number(props.potId)) ?? null)
const stats = computed(() => (pot.value ? goalStats(pot.value) : null))
const isGoal = computed(() => pot.value?.kind === 'goal')
const transfers = computed(() => (pot.value ? money.transfers[pot.value.id] ?? [] : []))
const backTo = computed(() => (pot.value?.is_archived ? { name: 'money-archive', label: 'Архив' } : { name: 'money-savings', label: 'Накопления' }))

async function loadHistory() {
  if (pot.value) await money.loadTransfers(pot.value.id)
}
onMounted(loadHistory)
watch(() => props.potId, loadHistory)

// --- moving money ---
const direction = ref<SavingsTransferDirection>('in')
const amount = ref('')
const transferDate = ref(todayIso())
const note = ref('')
const transferError = ref('')
const transferDone = ref('')
const submitting = ref(false)

const DIRECTIONS = computed(() =>
  [
    { value: 'in' as const, label: 'Отложить', button: 'Отложить', hint: 'Деньги уйдут из бюджета месяца в копилку.' },
    { value: 'out' as const, label: 'Снять', button: 'Снять в бюджет', hint: 'Деньги вернутся из копилки в бюджет месяца.' },
    { value: 'interest' as const, label: 'Проценты', button: 'Записать проценты', hint: 'Копилка вырастет, бюджет месяца не изменится.' },
  ].filter((d) => d.value !== 'interest' || !isGoal.value),
)
const currentDirection = computed(() => DIRECTIONS.value.find((d) => d.value === direction.value) ?? DIRECTIONS.value[0])

watch(direction, () => {
  transferError.value = ''
  transferDone.value = ''
})

async function submitTransfer() {
  if (!pot.value || !amount.value) return
  submitting.value = true
  transferError.value = ''
  transferDone.value = ''
  try {
    await money.addTransfer(pot.value.id, {
      direction: direction.value,
      amount: String(amount.value),
      transfer_date: transferDate.value,
      note: note.value.trim() || null,
    })
    transferDone.value = `${DIRECTION_LABELS[direction.value]} ${formatMoney(amount.value)}.`
    amount.value = ''
    note.value = ''
    // Moving money in or out changes the open month's balance too.
    await budget.refreshSummary()
  } catch {
    transferError.value =
      direction.value === 'out' ? 'Столько в копилке нет. Проверьте сумму.' : 'Перевод не сохранился. Попробуйте ещё раз.'
  } finally {
    submitting.value = false
  }
}

// --- history, grouped by month with the month's net change ---
const historyError = ref('')
const months = computed(() => {
  const groups: { key: string; label: string; net: number; items: SavingsTransfer[] }[] = []
  for (const t of transfers.value) {
    const key = t.transfer_date.slice(0, 7)
    let group = groups[groups.length - 1]
    if (!group || group.key !== key) {
      const [y, m] = key.split('-').map(Number)
      group = { key, label: `${MONTH_NAMES[m - 1]} ${y}`, net: 0, items: [] }
      groups.push(group)
    }
    group.items.push(t)
    group.net += (t.direction === 'out' ? -1 : 1) * toNumber(t.amount)
  }
  return groups
})

async function removeTransfer(transferId: number) {
  if (!pot.value) return
  historyError.value = ''
  try {
    await money.deleteTransfer(pot.value.id, transferId)
    await budget.refreshSummary()
  } catch {
    historyError.value = 'Эту запись нельзя удалить: баланс копилки ушёл бы в минус.'
  }
}

// --- the pot itself ---
const editing = ref(false)
const editName = ref('')
const editTarget = ref('')
const editDate = ref('')
const potError = ref('')

function startEditing() {
  if (!pot.value) return
  editName.value = pot.value.name
  editTarget.value = pot.value.target_amount ? String(toNumber(pot.value.target_amount)) : ''
  editDate.value = pot.value.target_date ?? ''
  potError.value = ''
  editing.value = true
}

async function savePot(archive: boolean) {
  if (!pot.value) return
  potError.value = ''
  const useForm = editing.value
  try {
    await money.updatePot(pot.value.id, {
      name: useForm ? editName.value.trim() || pot.value.name : pot.value.name,
      target_amount: useForm ? (editTarget.value ? String(editTarget.value) : null) : pot.value.target_amount,
      target_date: useForm ? editDate.value || null : pot.value.target_date,
      is_archived: archive,
    })
    editing.value = false
  } catch {
    potError.value = isGoal.value && useForm && !editTarget.value ? 'У цели должна быть сумма.' : 'Не сохранилось. Попробуйте ещё раз.'
  }
}

async function removePot() {
  if (!pot.value) return
  potError.value = ''
  try {
    await money.deletePot(pot.value.id)
    router.push({ name: 'money-savings' })
  } catch {
    potError.value = 'В копилке есть история переводов. Её можно убрать в архив.'
  }
}
</script>

<template>
  <div v-if="pot && stats" class="pot-page">
    <RouterLink :to="{ name: backTo.name }" class="back">
      <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3 5 8l5 5" /></svg>
      {{ backTo.label }}
    </RouterLink>

    <section class="notebook-sheet grid-paper" aria-labelledby="pot-name">
      <div class="sheet-body">
        <div class="figures">
          <p class="kind">
            {{ KIND_LABELS[pot.kind] }}<template v-if="pot.is_archived">, в архиве</template>
          </p>
          <h1 id="pot-name" class="pot-name">{{ pot.name }}</h1>
          <p :key="pot.balance" class="hand hand-figure num">
            {{ formatAmount(pot.balance) }}<span class="currency">₽</span>
          </p>

          <template v-if="isGoal && stats.target > 0">
            <GoalCells
              :share="stats.share"
              size="lg"
              :label="`Собрано ${formatMoney(stats.balance)} из ${formatMoney(stats.target)}`"
            />
            <p class="context">
              <template v-if="stats.reached">Цель собрана.</template>
              <template v-else>
                Осталось собрать <strong class="num">{{ formatMoney(stats.target - stats.balance) }}</strong> из
                <span class="num">{{ formatMoney(stats.target) }}</span>.
              </template>
              <template v-if="pot.target_date && stats.monthly">
                Чтобы успеть к {{ formatLongDate(pot.target_date) }}, откладывайте примерно
                <strong class="num">{{ formatMoney(stats.monthly.amount) }}</strong> в месяц
                ({{ stats.monthly.months }} {{ plural(stats.monthly.months, 'месяц', 'месяца', 'месяцев') }}).
              </template>
            </p>
          </template>
          <p v-else-if="stats.target > 0" class="context">
            Цель <span class="num">{{ formatMoney(stats.target) }}</span>, собрано {{ Math.floor(stats.share * 100) }}%.
          </p>
        </div>

        <div v-if="pot.is_archived" class="panel">
          <p>Копилка в архиве: её история сохранена, но деньги в неё не переводятся.</p>
          <button class="btn btn-primary" type="button" @click="savePot(false)">Вернуть из архива</button>
        </div>

        <form v-else class="panel" @submit.prevent="submitTransfer">
          <fieldset class="directions">
            <legend class="visually-hidden">Что сделать</legend>
            <label v-for="d in DIRECTIONS" :key="d.value" class="chip">
              <input v-model="direction" type="radio" name="pot-direction" :value="d.value" />
              <span>{{ d.label }}</span>
            </label>
          </fieldset>
          <p class="muted hint">{{ currentDirection.hint }}</p>
          <label class="amount-field">
            <span class="visually-hidden">Сумма в рублях</span>
            <input v-model="amount" type="number" inputmode="decimal" min="0.01" step="0.01" placeholder="0" required />
            <span class="amount-currency" aria-hidden="true">₽</span>
          </label>
          <div class="form-grid">
            <label class="field">
              Дата
              <input v-model="transferDate" type="date" required />
            </label>
            <label class="field">
              Комментарий
              <input v-model="note" type="text" maxlength="200" placeholder="Необязательно" />
            </label>
          </div>
          <button
            class="btn btn-primary submit"
            type="submit"
            :disabled="submitting || !amount || (direction === 'out' && stats.balance <= 0)"
          >
            {{ currentDirection.button }}
          </button>
          <p v-if="transferError" class="error-text" role="alert">{{ transferError }}</p>
          <p v-else-if="transferDone" class="done" role="status">{{ transferDone }}</p>
        </form>
      </div>
    </section>

    <section class="section" aria-labelledby="history-title">
      <div class="section-head">
        <h2 id="history-title">История</h2>
        <span v-if="transfers.length" class="muted">
          {{ transfers.length }} {{ plural(transfers.length, 'перевод', 'перевода', 'переводов') }}
        </span>
      </div>
      <p v-if="historyError" class="error-text" role="alert">{{ historyError }}</p>
      <p v-if="!transfers.length" class="empty">Переводов пока не было.</p>
      <div v-for="month in months" :key="month.key" class="month">
        <h3 class="month-head">
          <span>{{ month.label }}</span>
          <span class="num muted">{{ formatSignedMoney(month.net) }}</span>
        </h3>
        <ul class="transfers">
          <li v-for="t in month.items" :key="t.id" class="transfer">
            <span class="what">
              <span class="title">{{ DIRECTION_LABELS[t.direction] }}</span>
              <span class="meta">
                {{ formatShortDate(t.transfer_date) }}<template v-if="t.note">, {{ t.note }}</template>
              </span>
            </span>
            <span class="num amount" :class="`is-${t.direction}`">
              {{ t.direction === 'out' ? '−' : '+' }}{{ formatMoney(t.amount) }}
            </span>
            <ConfirmButton icon class="remove" confirm-label="Удалить перевод" @confirm="removeTransfer(t.id)" />
          </li>
        </ul>
      </div>
    </section>

    <section class="section" aria-labelledby="pot-settings-title">
      <div class="section-head">
        <h2 id="pot-settings-title">Копилка</h2>
      </div>
      <form v-if="editing" class="edit-form" @submit.prevent="savePot(pot.is_archived)" @keydown.esc="editing = false">
        <label class="field">
          Название
          <input v-model="editName" type="text" maxlength="100" required autofocus />
        </label>
        <div class="form-grid">
          <label class="field">
            {{ isGoal ? 'Сколько нужно, ₽' : 'Цель, ₽ (необязательно)' }}
            <input v-model="editTarget" type="number" inputmode="decimal" min="1" step="0.01" :required="isGoal" />
          </label>
          <label class="field">
            К какой дате
            <input v-model="editDate" type="date" />
          </label>
        </div>
        <div class="form-actions">
          <button class="btn btn-primary" type="submit">Сохранить</button>
          <button class="btn btn-quiet" type="button" @click="editing = false">Отмена</button>
        </div>
      </form>
      <div v-else class="pot-actions">
        <button class="btn" type="button" @click="startEditing">Изменить название и цель</button>
        <button v-if="!pot.is_archived" class="btn btn-quiet" type="button" @click="savePot(true)">Убрать в архив</button>
        <ConfirmButton v-if="stats.balance === 0 && !transfers.length" confirm-label="Удалить копилку" @confirm="removePot" />
      </div>
      <p v-if="!editing && !pot.is_archived" class="muted hint">
        В архив убирают собранные цели и закрытые вклады: история остаётся, копилка пропадает из текущих.
      </p>
      <p v-if="potError" class="error-text" role="alert">{{ potError }}</p>
    </section>
  </div>

  <div v-else class="missing">
    <p>Такой копилки нет. Возможно, её удалили.</p>
    <RouterLink :to="{ name: 'money-savings' }">К накоплениям</RouterLink>
  </div>
</template>

<style scoped>
.pot-page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.pot-page > .section {
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

.pot-name {
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

.panel {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.25rem;
  background: var(--sheet);
  border: 1px solid var(--line);
  border-radius: 12px;
}

.directions {
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

.transfers {
  list-style: none;
  margin: 0;
  padding: 0;
}

.transfer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto 2rem;
  align-items: center;
  column-gap: 0.75rem;
  padding: 0.5rem 0;
  border-bottom: 1px dashed var(--line);
}

.transfer:last-child {
  border-bottom: none;
}

.amount.is-in {
  color: var(--green);
}

.amount.is-out {
  color: var(--muted);
}

.amount.is-interest {
  color: var(--ink);
}

.transfer .amount {
  font-weight: 600;
  font-size: 1rem;
}

.pot-actions,
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
