<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  initialName?: string
  initialLimit?: string
  submitLabel: string
  showCancel?: boolean
}>()

const emit = defineEmits<{
  submit: [payload: { name: string; limit_amount: string }]
  cancel: []
}>()

const name = ref(props.initialName ?? '')
const limitAmount = ref(props.initialLimit ?? '')

function handleSubmit() {
  if (!name.value.trim() || !limitAmount.value) return
  emit('submit', { name: name.value.trim(), limit_amount: String(limitAmount.value) })
}
</script>

<template>
  <form class="category-form" @submit.prevent="handleSubmit" @keydown.esc="emit('cancel')">
    <label class="field name">
      Название
      <input v-model="name" type="text" placeholder="Например, продукты" required autofocus />
    </label>
    <label class="field limit">
      Лимит на месяц, ₽
      <input v-model="limitAmount" type="number" inputmode="decimal" min="0" step="0.01" placeholder="0" required />
    </label>
    <div class="actions">
      <button class="btn btn-primary" type="submit">{{ submitLabel }}</button>
      <button v-if="showCancel" class="btn btn-quiet" type="button" @click="emit('cancel')">Отмена</button>
    </div>
  </form>
</template>

<style scoped>
.category-form {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr) auto;
  gap: 0.75rem;
  align-items: end;
  padding: 1rem;
  background: var(--ink-wash);
  border-radius: 10px;
}

.actions {
  display: flex;
  gap: 0.25rem;
}

@media (max-width: 560px) {
  .category-form {
    grid-template-columns: 1fr;
  }
}
</style>
