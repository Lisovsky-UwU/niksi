<script setup lang="ts">
import { ref } from 'vue'
import { useBudgetStore } from '../stores/budget'
import CategoryForm from './CategoryForm.vue'
import CategoryRow from './CategoryRow.vue'

const store = useBudgetStore()
const showAddForm = ref(false)
const copying = ref(false)
const copyMessage = ref('')

async function handleAdd(payload: { name: string; limit_amount: string }) {
  await store.addCategory(payload)
  showAddForm.value = false
}

async function handleEdit(categoryId: number, payload: { name: string; limit_amount: string }) {
  await store.editCategory(categoryId, payload)
}

async function handleRemove(categoryId: number) {
  await store.removeCategory(categoryId)
}

async function handleCopyFromPrevious() {
  copying.value = true
  copyMessage.value = ''
  try {
    const before = store.categories.length
    await store.copyCategoriesFromPreviousMonth()
    if (store.categories.length === before) {
      copyMessage.value = 'В прошлом месяце не нашлось категорий для копирования.'
    }
  } catch {
    copyMessage.value = 'Не получилось скопировать категории. Проверьте, что прошлый месяц создан.'
  } finally {
    copying.value = false
  }
}
</script>

<template>
  <section id="categories" class="section" aria-labelledby="categories-title">
    <div class="section-head">
      <h2 id="categories-title">Категории</h2>
      <div class="head-actions">
        <button class="btn btn-quiet" type="button" :disabled="copying" @click="handleCopyFromPrevious">
          Скопировать из прошлого месяца
        </button>
        <button class="btn" type="button" :aria-expanded="showAddForm" @click="showAddForm = !showAddForm">
          Добавить категорию
        </button>
      </div>
    </div>

    <p v-if="copyMessage" class="muted" role="status">{{ copyMessage }}</p>

    <CategoryForm
      v-if="showAddForm"
      submit-label="Добавить"
      show-cancel
      @submit="handleAdd"
      @cancel="showAddForm = false"
    />

    <p v-if="(store.summary?.categories.length ?? 0) === 0 && !showAddForm" class="empty">
      В этом месяце пока нет категорий. Скопируйте их из прошлого месяца или добавьте новую.
    </p>

    <ul v-else class="rows">
      <CategoryRow
        v-for="category in store.summary?.categories ?? []"
        :key="category.id"
        :summary="category"
        @edit="(payload) => handleEdit(category.id, payload)"
        @remove="handleRemove(category.id)"
      />
    </ul>
  </section>
</template>

<style scoped>
.section {
  gap: 0.5rem;
}

.head-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.rows {
  list-style: none;
  margin: 0;
  padding: 0;
}
</style>
