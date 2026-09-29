<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref } from 'vue'

// Two-step destructive action inside the row itself, instead of a browser confirm().
const props = withDefaults(defineProps<{ label?: string; confirmLabel: string }>(), { label: 'Удалить' })
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
  <span class="confirm">
    <button v-if="!armed" class="btn btn-quiet" type="button" @click="arm">{{ props.label }}</button>
    <template v-else>
      <button ref="confirmRef" class="btn btn-danger" type="button" @click="confirm">{{ props.confirmLabel }}</button>
      <button class="btn btn-quiet" type="button" @click="cancel">Отмена</button>
    </template>
  </span>
</template>

<style scoped>
.confirm {
  display: inline-flex;
  gap: 0.25rem;
}

.btn {
  min-height: 2rem;
  padding: 0.25rem 0.6rem;
  font-size: 0.875rem;
}
</style>
