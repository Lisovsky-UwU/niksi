<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'

// A comment field that starts at a couple of lines and grows with the text, so a few
// words and a few sentences are both comfortable to write and to read back.
const model = defineModel<string>({ default: '' })
withDefaults(defineProps<{ placeholder?: string; maxlength?: number; rows?: number }>(), {
  placeholder: '',
  maxlength: 500,
  rows: 2,
})

const el = ref<HTMLTextAreaElement | null>(null)

function fit() {
  const area = el.value
  if (!area) return
  area.style.height = 'auto'
  area.style.height = `${area.scrollHeight + 2}px`
}

onMounted(fit)
watch(model, () => nextTick(fit))
</script>

<template>
  <textarea
    ref="el"
    v-model="model"
    class="growing"
    :rows="rows"
    :placeholder="placeholder"
    :maxlength="maxlength"
    @input="fit"
  />
</template>

<style scoped>
.growing {
  display: block;
  width: 100%;
  min-width: 0;
  resize: none;
  overflow: hidden;
  font: inherit;
  line-height: 1.45;
  color: var(--text);
  background: var(--sheet);
  border: 1px solid var(--line);
  border-radius: var(--radius-control);
  padding: 0.55rem 0.75rem;
}

.growing:hover {
  border-color: color-mix(in srgb, var(--ink) 40%, var(--line));
}

.growing:focus-visible {
  outline: none;
  border-color: var(--ink);
  box-shadow: 0 0 0 3px var(--ink-wash);
}
</style>
