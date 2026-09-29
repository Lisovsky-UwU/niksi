<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CategorySummary } from '../types/models'
import { formatMoney, toNumber } from '../utils/format'
import CategoryForm from './CategoryForm.vue'
import ConfirmButton from './ConfirmButton.vue'

const props = defineProps<{ summary: CategorySummary }>()
const emit = defineEmits<{
  edit: [payload: { name: string; limit_amount: string }]
  remove: []
}>()

const editing = ref(false)

const state = computed<'ok' | 'close' | 'over'>(() => {
  if (toNumber(props.summary.remaining) < 0) return 'over'
  if (props.summary.percent_used >= 80) return 'close'
  return 'ok'
})

function handleEdit(payload: { name: string; limit_amount: string }) {
  emit('edit', payload)
  editing.value = false
}
</script>

<template>
  <li class="category-row" :class="`is-${state}`">
    <CategoryForm
      v-if="editing"
      :initial-name="summary.name"
      :initial-limit="summary.limit_amount"
      submit-label="Сохранить"
      show-cancel
      @submit="handleEdit"
      @cancel="editing = false"
    />
    <template v-else>
      <div class="line">
        <span class="name"><span class="name-text">{{ summary.name }}</span></span>
        <span class="amounts">
          <span class="num spent">{{ formatMoney(summary.spent) }}</span>
          <span class="muted"> из </span>
          <span class="num muted">{{ formatMoney(summary.limit_amount) }}</span>
        </span>
      </div>

      <div class="bar" aria-hidden="true">
        <div class="bar-fill" :style="{ width: Math.min(summary.percent_used, 100) + '%' }" />
      </div>

      <div class="line footer">
        <span v-if="state === 'over'" class="remaining over">
          Перерасход <span class="num">{{ formatMoney(-toNumber(summary.remaining)) }}</span>
        </span>
        <span v-else class="remaining">
          Осталось <span class="num">{{ formatMoney(summary.remaining) }}</span>
        </span>
        <span class="actions">
          <button class="btn btn-quiet" type="button" @click="editing = true">Изменить</button>
          <ConfirmButton confirm-label="Удалить вместе с тратами" @confirm="emit('remove')" />
        </span>
      </div>
    </template>
  </li>
</template>

<style scoped>
.category-row {
  padding: 1rem 0 0.5rem;
  border-bottom: 1px solid var(--line);
}

.line {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem 1rem;
  flex-wrap: wrap;
}

.name {
  font-weight: 600;
  font-size: 1.05rem;
}

/* Highlighter swipe for categories close to their limit. */
.is-close .name-text {
  padding: 0 0.2em;
  margin: 0 -0.2em;
  background: linear-gradient(transparent 20%, var(--marker) 20%, var(--marker) 88%, transparent 88%);
  color: var(--marker-text);
  border-radius: 2px;
}

.spent {
  font-weight: 600;
}

.is-over .spent {
  color: var(--red);
}

.bar {
  margin: 0.5rem 0 0.35rem;
  height: 4px;
  border-radius: 2px;
  background: var(--line);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: var(--ink);
  border-radius: inherit;
  transition: width 0.4s ease;
}

.is-over .bar-fill {
  background: var(--red);
}

.footer {
  align-items: center;
}

.remaining {
  font-size: 0.9rem;
  color: var(--muted);
}

.remaining.over {
  color: var(--red);
  font-weight: 500;
}

.actions {
  display: inline-flex;
  gap: 0.25rem;
  margin-right: -0.5rem;
}

.actions > .btn {
  min-height: 2rem;
  padding: 0.25rem 0.6rem;
  font-size: 0.875rem;
}

@media (hover: hover) {
  .actions {
    opacity: 0.55;
    transition: opacity 0.15s;
  }

  .category-row:hover .actions,
  .actions:focus-within {
    opacity: 1;
  }
}
</style>
