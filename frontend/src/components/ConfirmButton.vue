<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref } from 'vue'

// Two-step destructive action inside the row itself, instead of a browser confirm().
// With `icon`, the first step is a small bin icon so list rows keep their width on phones;
// the confirmation then takes the whole row (see the `.is-armed` rules in list styles).
const props = withDefaults(defineProps<{ label?: string; confirmLabel: string; icon?: boolean }>(), {
  label: 'Удалить',
  icon: false,
})
const emit = defineEmits<{ confirm: [] }>()

const armed = ref(false)
const confirmRef = ref<HTMLButtonElement | null>(null)
let timer: number | undefined

async function arm() {
  armed.value = true
  window.clearTimeout(timer)
  timer = window.setTimeout(() => (armed.value = false), 5000)
  await nextTick()
  confirmRef.value?.focus()
}

function confirm() {
  window.clearTimeout(timer)
  armed.value = false
  emit('confirm')
}

function cancel() {
  window.clearTimeout(timer)
  armed.value = false
}

onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <span class="confirm" :class="{ 'is-armed': armed }">
    <template v-if="!armed">
      <button
        v-if="props.icon"
        class="icon-btn"
        type="button"
        :aria-label="props.label"
        :title="props.label"
        @click="arm"
      >
        <svg viewBox="0 0 16 16" aria-hidden="true">
          <path d="M3 4.5h10M6.5 4.5V3h3v1.5M4.5 4.5l.6 8.5h5.8l.6-8.5M6.8 7v4M9.2 7v4" />
        </svg>
      </button>
      <button v-else class="btn btn-quiet" type="button" @click="arm">{{ props.label }}</button>
    </template>
    <template v-else>
      <button ref="confirmRef" class="btn btn-danger" type="button" @click="confirm">{{ props.confirmLabel }}</button>
      <button class="btn btn-quiet" type="button" @click="cancel">Отмена</button>
    </template>
  </span>
</template>

<style scoped>
.confirm {
  display: inline-flex;
  justify-content: flex-end;
  gap: 0.25rem;
}

.btn {
  min-height: 2rem;
  padding: 0.25rem 0.6rem;
  font-size: 0.875rem;
}

.icon-btn {
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: var(--radius-control);
  background: transparent;
  color: var(--muted);
  cursor: pointer;
}

.icon-btn svg {
  width: 1rem;
  height: 1rem;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.icon-btn:hover {
  background: var(--red-wash);
  color: var(--red);
}
</style>
