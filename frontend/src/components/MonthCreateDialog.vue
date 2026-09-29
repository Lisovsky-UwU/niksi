<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMonthsStore } from '../stores/months'
import type { Month } from '../types/models'
import { MONTH_NAMES, monthLabel } from '../utils/format'

const props = defineProps<{ initialYear?: number; initialMonth?: number; showCancel?: boolean }>()
const store = useMonthsStore()
const emit = defineEmits<{ created: [month: Month]; cancel: [] }>()

function suggestNext(): { year: number; month: number } {
  if (props.initialYear && props.initialMonth) {
    return { year: props.initialYear, month: props.initialMonth }
  }
  if (store.months.length === 0) {
    const now = new Date()
    return { year: now.getFullYear(), month: now.getMonth() + 1 }
  }
  const latest = [...store.months].sort((a, b) => b.year * 12 + b.month - (a.year * 12 + a.month))[0]
  return latest.month === 12 ? { year: latest.year + 1, month: 1 } : { year: latest.year, month: latest.month + 1 }
}

const suggested = suggestNext()
const year = ref(suggested.year)
const month = ref(suggested.month)
const copyFromPrevious = ref(true)
const error = ref('')
const submitting = ref(false)

const exists = computed(() => store.months.some((m) => m.year === year.value && m.month === month.value))

async function handleSubmit() {
  error.value = ''
  if (exists.value) {
    error.value = `${monthLabel(year.value, month.value)} уже есть в списке.`
    return
  }
  submitting.value = true
  try {
    const created = await store.createMonth({
      year: year.value,
      month: month.value,
      copy_categories_from_previous: copyFromPrevious.value,
    })
    emit('created', created)
  } catch {
    error.value = 'Месяц не создался. Проверьте год и попробуйте ещё раз.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form class="month-create" @submit.prevent="handleSubmit" @keydown.esc="emit('cancel')">
    <div class="fields">
      <label class="field">
        Месяц
        <select v-model.number="month">
          <option v-for="(name, index) in MONTH_NAMES" :key="name" :value="index + 1">{{ name }}</option>
        </select>
      </label>
      <label class="field">
        Год
        <input v-model.number="year" type="number" min="2000" max="2100" required />
      </label>
    </div>
    <label class="checkbox">
      <input v-model="copyFromPrevious" type="checkbox" />
      Перенести категории, лимиты, ожидаемый доход и серую зону из предыдущего месяца
    </label>
    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    <div class="actions">
      <button class="btn btn-primary" type="submit" :disabled="submitting">
        Создать {{ monthLabel(year, month).toLowerCase() }}
      </button>
      <button v-if="showCancel" class="btn btn-quiet" type="button" @click="emit('cancel')">Отмена</button>
    </div>
  </form>
</template>

<style scoped>
.month-create {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.25rem;
  max-width: 28rem;
  background: var(--sheet);
  border: 1px solid var(--line);
  border-radius: 12px;
}

.fields {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  gap: 0.75rem;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.95rem;
  cursor: pointer;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}
</style>
