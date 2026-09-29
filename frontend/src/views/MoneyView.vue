<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterView } from 'vue-router'
import TabNav from '../components/TabNav.vue'
import { useMoneyStore } from '../stores/money'

// Layout for money that lives outside a single month: reconciliation and savings tabs.
const money = useMoneyStore()
const loading = ref(true)
const loadError = ref('')

const tabs = [
  { label: 'Сверка', to: { name: 'money' } },
  { label: 'Накопления', to: { name: 'money-savings' } },
]

onMounted(async () => {
  try {
    await money.load()
  } catch {
    loadError.value = 'Не удалось загрузить данные. Обновите страницу.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="money-page">
    <TabNav :tabs="tabs" label="Разделы денег" />
    <p v-if="loading" class="muted">Загружаем…</p>
    <p v-else-if="loadError" class="error-text">{{ loadError }}</p>
    <RouterView v-else />
  </div>
</template>

<style scoped>
.money-page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.money-page > :deep(.section) {
  width: 100%;
  max-width: 46rem;
}
</style>
