<script setup lang="ts">
import ExpenseList from '../components/ExpenseList.vue'
import MonthBalance from '../components/MonthBalance.vue'
import MonthHero from '../components/MonthHero.vue'
import { useBudgetStore } from '../stores/budget'

const store = useBudgetStore()
</script>

<template>
  <div v-if="store.summary" class="overview">
    <MonthHero :summary="store.summary" />

    <div class="columns">
      <MonthBalance />
      <ExpenseList :limit="5" title="Последние траты" />
    </div>
  </div>
</template>

<style scoped>
.overview {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.columns {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 1.5rem;
  align-items: start;
}

@media (max-width: 860px) {
  .columns {
    grid-template-columns: 1fr;
  }
}
</style>
