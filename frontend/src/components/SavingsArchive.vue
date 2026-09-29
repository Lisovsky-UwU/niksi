<script setup lang="ts">
import { computed } from 'vue'
import { useMoneyStore } from '../stores/money'
import { formatMoney, toNumber } from '../utils/format'
import SavingsPotItem from './SavingsPotItem.vue'

// Pots put away: finished goals, closed deposits. Kept for their history and can be brought back.
const money = useMoneyStore()
const left = computed(() => money.archivedPots.reduce((sum, p) => sum + toNumber(p.balance), 0))
</script>

<template>
  <section class="section archive" aria-labelledby="archive-title">
    <div class="section-head">
      <h2 id="archive-title">Архив накоплений</h2>
    </div>

    <p v-if="!money.archivedPots.length" class="empty">
      Здесь будут копилки, убранные в архив: собранные цели и закрытые вклады. Их история сохраняется,
      и любую можно вернуть обратно.
    </p>
    <template v-else>
      <p class="muted note">
        Архивные копилки не входят в «Всего отложено».
        <template v-if="left > 0">В них осталось <span class="num">{{ formatMoney(left) }}</span>.</template>
      </p>
      <ul class="pots">
        <SavingsPotItem v-for="pot in money.archivedPots" :key="pot.id" :pot="pot" />
      </ul>
    </template>
  </section>
</template>

<style scoped>
.note {
  font-size: 0.9rem;
}

.pots {
  list-style: none;
  margin: 0;
  padding: 0;
}
</style>
