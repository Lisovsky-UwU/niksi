<script setup lang="ts">
import { computed, ref } from 'vue'
import { useBudgetStore } from '../stores/budget'
import { useMonthsStore } from '../stores/months'
import { periodOf, allowedStartRange } from '../utils/periods'

// "с 5 сентября по 4 октября" under the month name, with a way to move the start to the
// day the salary actually came. Moving it also moves the end of the month before.
const budget = useBudgetStore()
const months = useMonthsStore()

const dayMonth = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' })
function format(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number)
  return dayMonth.format(new Date(y, m - 1, d))
}

const month = computed(() => budget.month)
const period = computed(() => (month.value ? periodOf(month.value) : null))
const range = computed(() => (month.value ? allowedStartRange(month.value.year, month.value.month) : null))

const editing = ref(false)
const start = ref('')
const saving = ref(false)
const error = ref('')

function startEditing() {
  if (!month.value) return
  start.value = month.value.start_date
  error.value = ''
  editing.value = true
}

async function save() {
  if (!month.value || !start.value) return
  saving.value = true
  error.value = ''
  try {
    await months.setStart(month.value.id, start.value)
    await budget.loadForMonth(month.value.id)
    editing.value = false
  } catch {
    error.value = 'Начало должно быть позже начала прошлого месяца и раньше начала следующего.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div v-if="period && month" class="period">
    <p v-if="!editing" class="dates">
      с {{ format(period.start) }} <template v-if="period.estimated">примерно </template>по {{ format(period.end) }}
      <button class="change" type="button" @click="startEditing">изменить начало</button>
    </p>
    <form v-else class="edit" @submit.prevent="save" @keydown.esc="editing = false">
      <label class="field">
        Месяц начинается
        <input v-model="start" type="date" :min="range?.min" :max="range?.max" required autofocus />
      </label>
      <div class="actions">
        <button class="btn btn-primary" type="submit" :disabled="saving">Сохранить</button>
        <button class="btn btn-quiet" type="button" @click="editing = false">Отмена</button>
      </div>
      <p class="muted hint">День первой полной зарплаты. Конец прошлого месяца сдвинется вместе с ним.</p>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    </form>
  </div>
</template>

<style scoped>
.dates {
  color: var(--muted);
  font-size: 0.925rem;
}

.change {
  margin-left: 0.35rem;
  padding: 0;
  border: none;
  background: none;
  color: var(--ink);
  font-size: inherit;
  cursor: pointer;
  text-decoration: underline;
  text-decoration-style: dotted;
  text-underline-offset: 0.2em;
}

.edit {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.5rem 0.75rem;
  max-width: 34rem;
  padding: 0.85rem 1rem;
  background: var(--ink-wash);
  border-radius: 10px;
}

.edit .field {
  flex: 0 1 12rem;
}

.actions {
  display: flex;
  gap: 0.25rem;
}

.hint,
.error-text {
  flex-basis: 100%;
  font-size: 0.85rem;
}
</style>
