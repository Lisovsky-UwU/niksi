<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useBudgetStore } from '../stores/budget'
import type { Expense } from '../types/models'
import { formatMoney, toNumber } from '../utils/format'
import ConfirmButton from './ConfirmButton.vue'
import GrowingTextarea from './GrowingTextarea.vue'
import PersonPicker from './PersonPicker.vue'
import UserAvatar from './UserAvatar.vue'

// One expense: what the money went on is the headline, the category and who wrote it
// sit underneath. Editing happens in place.
const props = defineProps<{ expense: Expense }>()
const store = useBudgetStore()
const auth = useAuthStore()

const categoryName = computed(
  () => store.categories.find((c) => c.id === props.expense.category_id)?.name ?? 'Без категории',
)
const spender = computed(() => store.userById(props.expense.spent_by_user_id))
// Only worth saying when someone else wrote it down.
const recordedBy = computed(() =>
  props.expense.created_by_user_id !== props.expense.spent_by_user_id
    ? store.userById(props.expense.created_by_user_id)
    : null,
)

// --- editing ---
const editing = ref(false)
const amount = ref('')
const categoryId = ref<number>(props.expense.category_id)
const expenseDate = ref('')
const description = ref('')
const spentBy = ref<number | null>(props.expense.spent_by_user_id)
const saving = ref(false)
const error = ref('')

function startEditing() {
  amount.value = String(toNumber(props.expense.amount))
  categoryId.value = props.expense.category_id
  expenseDate.value = props.expense.expense_date
  description.value = props.expense.description ?? ''
  spentBy.value = props.expense.spent_by_user_id
  error.value = ''
  editing.value = true
}

async function save() {
  if (!amount.value) return
  saving.value = true
  error.value = ''
  try {
    await store.editExpense(props.expense.id, {
      amount: String(amount.value),
      category_id: categoryId.value,
      expense_date: expenseDate.value,
      description: description.value.trim() || null,
      spent_by_user_id: spentBy.value ?? undefined,
    })
    editing.value = false
  } catch {
    error.value = 'Изменения не сохранились. Проверьте сумму и дату.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <li class="expense" :class="{ 'is-editing': editing }">
    <form v-if="editing" class="edit-form" @submit.prevent="save" @keydown.esc="editing = false">
      <div class="form-grid">
        <label class="field">
          Сумма, ₽
          <input v-model="amount" type="number" inputmode="decimal" min="0.01" step="0.01" required autofocus />
        </label>
        <label class="field">
          Дата
          <input v-model="expenseDate" type="date" required />
        </label>
      </div>
      <fieldset class="chips">
        <legend class="visually-hidden">Категория</legend>
        <label
          v-for="category in store.categories"
          :key="category.id"
          class="chip cat-chip"
          :style="{ '--cat': store.categoryColor(category.id) }"
        >
          <input v-model="categoryId" type="radio" :name="`edit-category-${expense.id}`" :value="category.id" />
          <span>{{ category.name }}</span>
        </label>
      </fieldset>
      <PersonPicker
        v-if="store.users.length > 1"
        v-model="spentBy"
        :users="store.users"
        :me-id="auth.user?.id"
        label="Кто потратил"
        :name="`edit-spent-by-${expense.id}`"
      />
      <label class="field">
        На что потратили
        <GrowingTextarea v-model="description" placeholder="Пара слов или пара предложений" />
      </label>
      <div class="form-actions">
        <button class="btn btn-primary" type="submit" :disabled="saving">Сохранить</button>
        <button class="btn btn-quiet" type="button" @click="editing = false">Отмена</button>
      </div>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    </form>

    <template v-else>
      <UserAvatar class="who" :user="spender" size="sm" />
      <div class="body">
        <p v-if="expense.description" class="comment">{{ expense.description }}</p>
        <span class="category" :class="{ 'is-headline': !expense.description }">
          <span class="cat-mark" :style="{ '--cat': store.categoryColor(expense.category_id) }">{{ categoryName }}</span>
        </span>
        <span v-if="recordedBy" class="meta">записано: {{ recordedBy.display_name }}</span>
      </div>
      <span class="num amount">{{ formatMoney(expense.amount) }}</span>
      <div class="tools">
        <button class="icon-btn" type="button" aria-label="Изменить трату" title="Изменить" @click="startEditing">
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <path d="M10.8 2.7 13.3 5.2 6 12.5 3 13l.5-3 7.3-7.3ZM9.6 3.9l2.5 2.5" />
          </svg>
        </button>
        <ConfirmButton icon class="remove" confirm-label="Удалить трату" @confirm="store.removeExpense(expense.id)" />
      </div>
    </template>
  </li>
</template>

<style scoped>
.expense {
  display: grid;
  grid-template-columns: 1.6rem minmax(0, 1fr) auto;
  grid-template-areas:
    'who body amount'
    'who body tools';
  column-gap: 0.75rem;
  align-items: start;
  padding: 0.7rem 0;
  border-bottom: 1px dashed var(--line);
}

.expense:last-child {
  border-bottom: none;
}

.who {
  grid-area: who;
  margin-top: 0.1rem;
}

.body {
  grid-area: body;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

/* What the money went on: the line you read first, kept whole even when it is long. */
.comment {
  font-weight: 500;
  line-height: 1.4;
  white-space: pre-line;
  overflow-wrap: anywhere;
}

.category {
  font-size: 0.85rem;
}

.category.is-headline {
  font-size: 1rem;
  font-weight: 500;
}

.amount {
  grid-area: amount;
  font-weight: 600;
  text-align: right;
}

.tools {
  grid-area: tools;
  display: flex;
  justify-content: flex-end;
  margin-right: -0.4rem;
}

/* Once the bin is pressed, the confirmation gets a line of its own under the expense. */
.tools:has(.is-armed) {
  grid-area: auto;
  grid-column: 1 / -1;
  grid-row: 3;
  margin-top: 0.25rem;
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
  stroke-linejoin: round;
}

.icon-btn:hover {
  background: var(--ink-wash);
  color: var(--ink);
}

.is-editing {
  display: block;
}

.edit-form {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--ink-wash);
  border-radius: 10px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0;
  padding: 0;
  border: none;
}

.form-actions {
  display: flex;
  gap: 0.25rem;
}
</style>
