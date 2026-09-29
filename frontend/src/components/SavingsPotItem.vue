<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useBudgetStore } from '../stores/budget'
import { useMoneyStore } from '../stores/money'
import type { SavingsPot, SavingsTransferDirection } from '../types/models'
import { formatLongDate, formatMoney, formatShortDate, plural, todayIso, toNumber } from '../utils/format'
import ConfirmButton from './ConfirmButton.vue'

const props = defineProps<{ pot: SavingsPot }>()
const money = useMoneyStore()
const budget = useBudgetStore()

const KIND_LABELS = { account: 'Накопительный счёт', deposit: 'Вклад', goal: 'Цель' } as const
const CELLS = 20

// Skip the kind when the name already says it ("Накопительный счёт").
const kindLabel = computed(() => {
  const parts: string[] = []
  const kind = KIND_LABELS[props.pot.kind]
  if (kind.toLowerCase() !== props.pot.name.trim().toLowerCase()) parts.push(kind)
  if (props.pot.is_archived) parts.push('в архиве')
  return parts.join(', ')
})

const balance = computed(() => toNumber(props.pot.balance))
const target = computed(() => toNumber(props.pot.target_amount))
const isGoal = computed(() => props.pot.kind === 'goal')
const reached = computed(() => target.value > 0 && balance.value >= target.value)
const filledCells = computed(() =>
  target.value > 0 ? Math.min(CELLS, Math.floor((balance.value / target.value) * CELLS)) : 0,
)

// How much to put aside each month to reach the goal by its date.
const monthlyNeeded = computed(() => {
  if (!props.pot.target_date || reached.value || target.value <= 0) return null
  const [y, m] = props.pot.target_date.split('-').map(Number)
  const now = new Date()
  const months = Math.max(1, (y - now.getFullYear()) * 12 + (m - (now.getMonth() + 1)))
  return { months, amount: Math.ceil((target.value - balance.value) / months) }
})

// --- transfers ---
const mode = ref<SavingsTransferDirection | 'edit' | null>(null)
const amount = ref('')
const transferDate = ref(todayIso())
const note = ref('')
const error = ref('')
const submitting = ref(false)

const TRANSFER_COPY: Record<SavingsTransferDirection, { title: string; button: string }> = {
  in: { title: 'Сколько откладываете, ₽', button: 'Отложить' },
  out: { title: 'Сколько снимаете в бюджет, ₽', button: 'Снять' },
  interest: { title: 'Сколько начислил банк, ₽', button: 'Записать проценты' },
}

watch(mode, () => {
  error.value = ''
  amount.value = ''
  note.value = ''
  transferDate.value = todayIso()
})

async function submitTransfer() {
  if (!mode.value || mode.value === 'edit' || !amount.value) return
  submitting.value = true
  error.value = ''
  try {
    await money.addTransfer(props.pot.id, {
      direction: mode.value,
      amount: String(amount.value),
      transfer_date: transferDate.value,
      note: note.value.trim() || null,
    })
    mode.value = null
    // Moving money in or out changes the open month's balance too.
    await budget.refreshSummary()
  } catch {
    error.value =
      mode.value === 'out' ? 'Столько в копилке нет. Проверьте сумму.' : 'Перевод не сохранился. Попробуйте ещё раз.'
  } finally {
    submitting.value = false
  }
}

// --- history ---
const historyOpen = ref(false)
async function toggleHistory() {
  historyOpen.value = !historyOpen.value
  if (historyOpen.value) await money.loadTransfers(props.pot.id)
}

async function removeTransfer(transferId: number) {
  error.value = ''
  try {
    await money.deleteTransfer(props.pot.id, transferId)
    await budget.refreshSummary()
  } catch {
    error.value = 'Эту запись нельзя удалить: баланс копилки ушёл бы в минус.'
  }
}

const DIRECTION_LABELS: Record<SavingsTransferDirection, string> = {
  in: 'Отложили',
  out: 'Сняли',
  interest: 'Проценты',
}

// --- edit ---
const editName = ref('')
const editTarget = ref('')
const editDate = ref('')

watch(mode, (value) => {
  if (value === 'edit') {
    editName.value = props.pot.name
    editTarget.value = props.pot.target_amount ? String(toNumber(props.pot.target_amount)) : ''
    editDate.value = props.pot.target_date ?? ''
  }
})

async function saveEdit(archive = props.pot.is_archived) {
  error.value = ''
  try {
    await money.updatePot(props.pot.id, {
      name: editName.value.trim() || props.pot.name,
      target_amount: editTarget.value ? String(editTarget.value) : null,
      target_date: editDate.value || null,
      is_archived: archive,
    })
    mode.value = null
  } catch {
    error.value = isGoal.value && !editTarget.value ? 'У цели должна быть сумма.' : 'Не сохранилось. Попробуйте ещё раз.'
  }
}

async function removePot() {
  error.value = ''
  try {
    await money.deletePot(props.pot.id)
  } catch {
    error.value = 'В копилке есть история переводов. Её можно убрать в архив.'
  }
}
</script>

<template>
  <li class="pot" :class="{ archived: pot.is_archived, goal: isGoal }">
    <div class="top">
      <div class="title">
        <h3 class="name">{{ pot.name }}</h3>
        <span v-if="kindLabel" class="kind muted">{{ kindLabel }}</span>
      </div>
      <span class="num balance">{{ formatMoney(pot.balance) }}</span>
    </div>

    <template v-if="isGoal && target > 0">
      <div class="cells" role="meter" :aria-valuenow="balance" aria-valuemin="0" :aria-valuemax="target"
        :aria-label="`Собрано ${formatMoney(balance)} из ${formatMoney(target)}`">
        <span v-for="i in CELLS" :key="i" class="cell" :class="{ filled: i <= filledCells }" />
      </div>
      <p class="goal-text">
        <template v-if="reached">Цель собрана.</template>
        <template v-else>
          Осталось собрать <strong class="num">{{ formatMoney(target - balance) }}</strong> из
          <span class="num">{{ formatMoney(target) }}</span>.
        </template>
        <template v-if="pot.target_date && monthlyNeeded">
          Чтобы успеть к {{ formatLongDate(pot.target_date) }}, откладывайте примерно
          <strong class="num">{{ formatMoney(monthlyNeeded.amount) }}</strong> в месяц
          ({{ monthlyNeeded.months }} {{ plural(monthlyNeeded.months, 'месяц', 'месяца', 'месяцев') }}).
        </template>
      </p>
    </template>

    <div v-if="mode === null && !pot.is_archived" class="actions">
      <button class="btn btn-primary small" type="button" @click="mode = 'in'">Отложить</button>
      <button class="btn small" type="button" :disabled="balance <= 0" @click="mode = 'out'">Снять</button>
      <button v-if="!isGoal" class="btn btn-quiet small" type="button" @click="mode = 'interest'">Проценты</button>
      <button class="btn btn-quiet small" type="button" :aria-expanded="historyOpen" @click="toggleHistory">
        История
      </button>
      <button class="btn btn-quiet small" type="button" @click="mode = 'edit'">Изменить</button>
    </div>
    <div v-else-if="mode === null" class="actions">
      <button class="btn btn-quiet small" type="button" @click="saveEdit(false)">Вернуть из архива</button>
      <button class="btn btn-quiet small" type="button" :aria-expanded="historyOpen" @click="toggleHistory">
        История
      </button>
    </div>

    <form
      v-if="mode === 'in' || mode === 'out' || mode === 'interest'"
      class="inline-form"
      @submit.prevent="submitTransfer"
      @keydown.esc="mode = null"
    >
      <div class="form-grid">
        <label class="field">
          {{ TRANSFER_COPY[mode].title }}
          <input v-model="amount" type="number" inputmode="decimal" min="0.01" step="0.01" required autofocus />
        </label>
        <label class="field">
          Дата
          <input v-model="transferDate" type="date" required />
        </label>
      </div>
      <label class="field">
        Комментарий
        <input v-model="note" type="text" maxlength="200" placeholder="Необязательно" />
      </label>
      <p v-if="mode === 'interest'" class="muted small-text">Проценты увеличивают копилку, но не трогают бюджет.</p>
      <div class="form-actions">
        <button class="btn btn-primary" type="submit" :disabled="submitting">{{ TRANSFER_COPY[mode].button }}</button>
        <button class="btn btn-quiet" type="button" @click="mode = null">Отмена</button>
      </div>
    </form>

    <form v-if="mode === 'edit'" class="inline-form" @submit.prevent="saveEdit()" @keydown.esc="mode = null">
      <label class="field">
        Название
        <input v-model="editName" type="text" maxlength="100" required />
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
        <button class="btn btn-quiet" type="button" @click="saveEdit(true)">Убрать в архив</button>
        <ConfirmButton v-if="balance === 0" confirm-label="Удалить копилку" @confirm="removePot" />
        <button class="btn btn-quiet" type="button" @click="mode = null">Отмена</button>
      </div>
    </form>

    <p v-if="error" class="error-text" role="alert">{{ error }}</p>

    <div v-if="historyOpen" class="history">
      <p v-if="!money.transfers[pot.id]?.length" class="muted small-text">Переводов пока не было.</p>
      <ul v-else class="transfers">
        <li v-for="t in money.transfers[pot.id]" :key="t.id" class="transfer">
          <span class="what">
            <span class="title">{{ DIRECTION_LABELS[t.direction] }}</span>
            <span class="meta">
              {{ formatShortDate(t.transfer_date) }}<template v-if="t.note">, {{ t.note }}</template>
            </span>
          </span>
          <span class="num amount" :class="{ out: t.direction === 'out' }">
            {{ t.direction === 'out' ? '−' : '+' }}{{ formatMoney(t.amount) }}
          </span>
          <ConfirmButton icon class="remove" confirm-label="Удалить перевод" @confirm="removeTransfer(t.id)" />
        </li>
      </ul>
    </div>
  </li>
</template>

<style scoped>
.pot {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 1rem 0 1.1rem;
  border-bottom: 1px solid var(--line);
}

.archived {
  opacity: 0.7;
}

.top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
}

.name {
  font-size: 1.1rem;
}

.kind {
  font-size: 0.85rem;
}

.balance {
  font-size: 1.35rem;
  font-weight: 600;
}

/* Savings tracker drawn as notebook cells being coloured in. */
.cells {
  display: grid;
  grid-template-columns: repeat(20, minmax(0, 1fr));
  max-width: calc(20 * 1.2rem);
  border-top: 1px solid var(--grid);
  border-left: 1px solid var(--grid);
}

.cell {
  aspect-ratio: 1;
  border-right: 1px solid var(--grid);
  border-bottom: 1px solid var(--grid);
  background: var(--sheet);
}

.cell.filled {
  background: repeating-linear-gradient(
    -45deg,
    var(--ink) 0 2px,
    color-mix(in srgb, var(--ink) 55%, transparent) 2px 4px
  );
}

.goal-text {
  font-size: 0.925rem;
  color: var(--muted);
  max-width: 36rem;
}

.goal-text strong {
  color: var(--text);
  font-weight: 600;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-left: -0.1rem;
}

.small {
  min-height: 2rem;
  padding: 0.25rem 0.75rem;
  font-size: 0.9rem;
}

.inline-form {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--ink-wash);
  border-radius: 10px;
}

.form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.small-text {
  font-size: 0.875rem;
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
  gap: 0.75rem;
  padding: 0.35rem 0;
  border-bottom: 1px dashed var(--line);
  font-size: 0.925rem;
}

.transfer:last-child {
  border-bottom: none;
}

.date {
  font-size: 0.85rem;
}

.amount {
  font-weight: 600;
}

.amount.out {
  color: var(--muted);
}
</style>
