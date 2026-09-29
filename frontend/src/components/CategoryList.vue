<script setup lang="ts">
import { computed, ref } from 'vue'
import { listCategories } from '../api/categories'
import { useBudgetStore } from '../stores/budget'
import { useMonthsStore } from '../stores/months'
import type { Category } from '../types/models'
import { monthIn, monthOf, plural } from '../utils/format'
import CategoryForm, { type CategoryFormPayload } from './CategoryForm.vue'
import CategoryRow from './CategoryRow.vue'

const store = useBudgetStore()
const months = useMonthsStore()
const showAddForm = ref(false)
const copying = ref(false)
const copyMessage = ref('')

async function handleAdd(payload: CategoryFormPayload) {
  await store.addCategory(payload)
  showAddForm.value = false
}

async function handleEdit(categoryId: number, payload: CategoryFormPayload) {
  await store.editCategory(categoryId, { ...payload, color: payload.color ?? 'auto' })
}

async function handleRemove(categoryId: number) {
  await store.removeCategory(categoryId)
}

// --- copying from the previous month ---
// When the month already has categories, copying first asks: it lists what would be
// added (only names the month does not have yet) and waits for a confirmation.
const previousMonth = computed(() => {
  const current = store.month
  if (!current) return null
  return (
    [...months.months]
      .filter((m) => m.year * 12 + m.month < current.year * 12 + current.month)
      .sort((a, b) => b.year * 12 + b.month - (a.year * 12 + a.month))[0] ?? null
  )
})
const pendingCopy = ref<Category[] | null>(null)

async function doCopy() {
  copying.value = true
  copyMessage.value = ''
  try {
    const before = store.categories.length
    await store.copyCategoriesFromPreviousMonth()
    const added = store.categories.length - before
    copyMessage.value = added
      ? `Добавлено ${added} ${plural(added, 'категория', 'категории', 'категорий')}.`
      : 'В прошлом месяце не нашлось категорий для копирования.'
  } catch {
    copyMessage.value = 'Не получилось скопировать категории. Проверьте, что прошлый месяц создан.'
  } finally {
    copying.value = false
    pendingCopy.value = null
  }
}

async function handleCopyFromPrevious() {
  copyMessage.value = ''
  if (!store.categories.length) {
    await doCopy()
    return
  }
  if (!previousMonth.value) {
    copyMessage.value = 'Прошлого месяца ещё нет, копировать неоткуда.'
    return
  }
  copying.value = true
  try {
    const existing = new Set(store.categories.map((c) => c.name.trim().toLowerCase()))
    const source = await listCategories(previousMonth.value.id)
    pendingCopy.value = source.filter((c) => !existing.has(c.name.trim().toLowerCase()))
  } catch {
    copyMessage.value = 'Не получилось загрузить категории прошлого месяца.'
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
        <button
          class="btn btn-quiet"
          type="button"
          :disabled="copying || pendingCopy !== null"
          @click="handleCopyFromPrevious"
        >
          Скопировать из прошлого месяца
        </button>
        <button class="btn" type="button" :aria-expanded="showAddForm" @click="showAddForm = !showAddForm">
          Добавить категорию
        </button>
      </div>
    </div>

    <!-- A note in the margin: what copying would do, and a button to go ahead. -->
    <div v-if="pendingCopy !== null && previousMonth && store.month" class="copy-note" role="alertdialog" aria-labelledby="copy-note-text">
      <template v-if="pendingCopy.length">
        <p id="copy-note-text">
          В {{ monthIn(store.month.month) }} уже есть {{ store.categories.length }}
          {{ plural(store.categories.length, 'категория', 'категории', 'категорий') }}.
          Из {{ monthOf(previousMonth.month) }} добавятся только те, которых ещё нет:
        </p>
        <ul class="copy-list">
          <li v-for="c in pendingCopy" :key="c.id">{{ c.name }}</li>
        </ul>
        <div class="copy-actions">
          <button class="btn btn-primary" type="button" :disabled="copying" @click="doCopy">
            Добавить {{ pendingCopy.length }} {{ plural(pendingCopy.length, 'категорию', 'категории', 'категорий') }}
          </button>
          <button class="btn btn-quiet" type="button" @click="pendingCopy = null">Отмена</button>
        </div>
      </template>
      <template v-else>
        <p id="copy-note-text">
          Все категории {{ monthOf(previousMonth.month) }} уже есть в {{ monthIn(store.month.month) }}, копировать нечего.
        </p>
        <div class="copy-actions">
          <button class="btn" type="button" @click="pendingCopy = null">Понятно</button>
        </div>
      </template>
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

/* Written in the margin with the amber pencil: worth reading before going ahead. */
.copy-note {
  display: grid;
  gap: 0.6rem;
  margin-top: 0.5rem;
  padding: 0.9rem 1rem;
  border-left: 3px solid var(--amber);
  border-radius: 0 10px 10px 0;
  background: color-mix(in srgb, var(--amber) 12%, var(--sheet));
}

.copy-list {
  margin: 0;
  padding-left: 1.2rem;
  columns: 2 10rem;
  font-weight: 500;
}

.copy-actions {
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
