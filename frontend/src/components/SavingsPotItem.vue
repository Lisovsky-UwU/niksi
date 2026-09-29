<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import type { SavingsPot } from '../types/models'
import { formatMoney } from '../utils/format'
import { goalStats, kindLabel } from '../utils/savings'
import GoalCells from './GoalCells.vue'

// A pot in the savings list: a quiet row that opens the pot's own page.
const props = defineProps<{ pot: SavingsPot }>()
const stats = computed(() => goalStats(props.pot))
const isGoal = computed(() => props.pot.kind === 'goal' && stats.value.target > 0)
</script>

<template>
  <li>
    <RouterLink :to="{ name: 'money-pot', params: { potId: pot.id } }" class="pot">
      <span class="title">
        <span class="name">{{ pot.name }}</span>
        <span v-if="kindLabel(pot)" class="meta">{{ kindLabel(pot) }}</span>
      </span>
      <span class="num balance">{{ formatMoney(pot.balance) }}</span>
      <svg class="chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="m6 3 5 5-5 5" /></svg>

      <span v-if="isGoal" class="goal">
        <GoalCells :share="stats.share" :label="`Собрано ${formatMoney(stats.balance)} из ${formatMoney(stats.target)}`" />
        <span class="meta">
          <template v-if="stats.reached">Цель собрана</template>
          <template v-else>собрано {{ Math.floor(stats.share * 100) }}% из {{ formatMoney(stats.target) }}</template>
        </span>
      </span>
    </RouterLink>
  </li>
</template>

<style scoped>
.pot {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto 1rem;
  align-items: center;
  gap: 0.5rem 0.75rem;
  padding: 0.85rem 0.75rem;
  margin: 0 -0.75rem;
  border-bottom: 1px solid var(--line);
  border-radius: 10px;
  color: var(--text);
  text-decoration: none;
  transition: background-color 0.15s;
}

li:last-child .pot {
  border-bottom: none;
}

.pot:hover {
  background: var(--ink-wash);
}

.title {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.name {
  font-weight: 600;
  font-size: 1.05rem;
  overflow-wrap: anywhere;
}

.balance {
  font-weight: 600;
  font-size: 1.1rem;
}

.chevron {
  width: 1rem;
  height: 1rem;
  fill: none;
  stroke: var(--muted);
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.pot:hover .chevron {
  stroke: var(--ink);
}

.goal {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 0.75rem;
}
</style>
