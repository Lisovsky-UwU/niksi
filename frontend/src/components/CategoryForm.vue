<script setup lang="ts">
import { ref } from 'vue'
import type { CategoryColor } from '../types/models'
import { CATEGORY_COLORS, categoryColorVar } from '../utils/categoryColors'

export interface CategoryFormPayload {
  name: string
  limit_amount: string
  /** null: pick automatically */
  color: CategoryColor | null
}

const props = defineProps<{
  initialName?: string
  initialLimit?: string
  initialColor?: CategoryColor | null
  submitLabel: string
  showCancel?: boolean
}>()

const emit = defineEmits<{
  submit: [payload: CategoryFormPayload]
  cancel: []
}>()

const name = ref(props.initialName ?? '')
const limitAmount = ref(props.initialLimit ?? '')
const color = ref<CategoryColor | 'auto'>(props.initialColor ?? 'auto')

function handleSubmit() {
  if (!name.value.trim() || !limitAmount.value) return
  emit('submit', {
    name: name.value.trim(),
    limit_amount: String(limitAmount.value),
    color: color.value === 'auto' ? null : color.value,
  })
}
</script>

<template>
  <form class="category-form" @submit.prevent="handleSubmit" @keydown.esc="emit('cancel')">
    <div class="form-grid">
      <label class="field">
        Название
        <input v-model="name" type="text" placeholder="Например, продукты" required autofocus />
      </label>
      <label class="field">
        Лимит на месяц, ₽
        <input v-model="limitAmount" type="number" inputmode="decimal" min="0" step="0.01" placeholder="0" required />
      </label>
    </div>

    <!-- Colours drawn as highlighter strokes: the same mark the category gets in the lists. -->
    <fieldset class="colors">
      <legend class="field-legend">Цвет</legend>
      <div class="swatches">
        <label class="swatch auto" title="Автоматически">
          <input v-model="color" type="radio" name="category-color" value="auto" />
          <span>Авто</span>
        </label>
        <label
          v-for="option in CATEGORY_COLORS"
          :key="option.key"
          class="swatch"
          :title="option.label"
          :style="{ '--cat': categoryColorVar(option.key) }"
        >
          <input v-model="color" type="radio" name="category-color" :value="option.key" />
          <span class="stroke"><span class="visually-hidden">{{ option.label }}</span></span>
        </label>
      </div>
    </fieldset>

    <div class="actions">
      <button class="btn btn-primary" type="submit">{{ submitLabel }}</button>
      <button v-if="showCancel" class="btn btn-quiet" type="button" @click="emit('cancel')">Отмена</button>
    </div>
  </form>
</template>

<style scoped>
.category-form {
  display: grid;
  gap: 0.9rem;
  padding: 1rem;
  background: var(--ink-wash);
  border-radius: 10px;
}

.colors {
  margin: 0;
  padding: 0;
  border: none;
  min-width: 0;
}

.field-legend {
  padding: 0;
  margin-bottom: 0.4rem;
  font-size: 0.875rem;
  color: var(--muted);
}

.swatches {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
}

.swatch {
  position: relative;
  cursor: pointer;
}

.swatch input {
  position: absolute;
  opacity: 0;
  width: 1px;
  height: 1px;
}

/* A short, slightly slanted highlighter stroke. */
.stroke {
  display: block;
  width: 2.25rem;
  height: 1.35rem;
  border-radius: 3px 6px 4px 7px;
  /* Samples are laid on thicker than the marks in lists, so the pencils are easy to tell apart. */
  background: color-mix(in srgb, var(--cat) 78%, transparent);
  transform: skewX(-12deg);
  outline: 2px solid transparent;
  outline-offset: 2px;
  transition: outline-color 0.15s, transform 0.15s;
}

.swatch:hover .stroke {
  transform: skewX(-12deg) scale(1.08);
}

.auto span {
  display: block;
  padding: 0.1rem 0.6rem;
  border: 1px dashed var(--muted);
  border-radius: 6px;
  font-size: 0.85rem;
  color: var(--muted);
  outline: 2px solid transparent;
  outline-offset: 2px;
}

.swatch input:checked + .stroke,
.swatch input:checked + span {
  outline-color: var(--ink);
}

.auto input:checked + span {
  color: var(--ink);
  border-color: var(--ink);
}

.swatch input:focus-visible + span {
  outline-color: var(--ink);
  outline-style: dashed;
}

.actions {
  display: flex;
  gap: 0.25rem;
}
</style>
