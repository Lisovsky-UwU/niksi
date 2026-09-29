<script setup lang="ts">
import { computed } from 'vue'

// A savings tracker drawn as a row of notebook cells being coloured in.
const props = withDefaults(defineProps<{ share: number; label: string; cells?: number; size?: 'sm' | 'lg' }>(), {
  cells: 20,
  size: 'sm',
})
const filled = computed(() => Math.floor(Math.min(1, Math.max(0, props.share)) * props.cells))
</script>

<template>
  <div
    class="cells"
    :class="`is-${size}`"
    :style="{ '--cells': cells }"
    role="meter"
    :aria-valuenow="Math.round(share * 100)"
    aria-valuemin="0"
    aria-valuemax="100"
    :aria-label="label"
  >
    <span v-for="i in cells" :key="i" class="cell" :class="{ filled: i <= filled }" />
  </div>
</template>

<style scoped>
.cells {
  --cell-size: 1.2rem;
  /* Ruled darker than the paper's own grid, so the tracker reads even on a squared sheet. */
  --rule: color-mix(in srgb, var(--ink) 35%, var(--line));
  display: grid;
  grid-template-columns: repeat(var(--cells), minmax(0, 1fr));
  width: 100%;
  max-width: calc(var(--cells) * var(--cell-size));
  border-top: 1px solid var(--rule);
  border-left: 1px solid var(--rule);
}

.is-sm {
  --cell-size: 0.8rem;
}

.is-lg {
  --cell-size: 1.6rem;
}

.cell {
  aspect-ratio: 1;
  border-right: 1px solid var(--rule);
  border-bottom: 1px solid var(--rule);
  background: var(--sheet);
}

.cell.filled {
  background: repeating-linear-gradient(
    -45deg,
    var(--ink) 0 2px,
    color-mix(in srgb, var(--ink) 55%, transparent) 2px 4px
  );
}
</style>
