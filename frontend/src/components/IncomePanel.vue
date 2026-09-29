<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useBudgetStore } from '../stores/budget'
import { formatMoney, formatShortDate, todayIso, toNumber } from '../utils/format'
import ConfirmButton from './ConfirmButton.vue'
import UserAvatar from './UserAvatar.vue'

const auth = useAuthStore()
const store = useBudgetStore()

const perUser = computed(() => store.summary?.income.per_user ?? [])
const myId = computed(() => auth.user?.id ?? null)

// --- expected income (my own) ---
const editingForecast = ref(false)
const forecastAmount = ref('')
const myForecast = computed(() => perUser.value.find((u) => u.user_id === myId.value)?.forecast ?? '0')
watch(editingForecast, (open) => {
  if (open) forecastAmount.value = toNumber(myForecast.value) ? String(toNumber(myForecast.value)) : ''
})

async function saveForecast() {
  await store.setMyIncome(String(forecastAmount.value || '0'))
  editingForecast.value = false
}

// --- actual receipts ---
const showEntryForm = ref(false)
const entryAmount = ref('')
const entryDescription = ref('')
const entryDate = ref(todayIso())
const entryUserId = ref<number | null>(null)
const submitting = ref(false)
const error = ref('')

watch(showEntryForm, (open) => {
  if (open) entryUserId.value = myId.value
})

async function addEntry() {
  if (!entryAmount.value) return
  error.value = ''
  submitting.value = true
  try {
    await store.addIncomeEntry({
      amount: String(entryAmount.value),
      description: entryDescription.value.trim() || null,
      received_date: entryDate.value,
      user_id: entryUserId.value ?? undefined,
    })
    entryAmount.value = ''
    entryDescription.value = ''
    showEntryForm.value = false
  } catch {
    error.value = 'Поступление не сохранилось. Проверьте сумму и попробуйте ещё раз.'
  } finally {
    submitting.value = false
  }
}

function progress(actual: string, forecast: string): number {
  const f = toNumber(forecast)
  return f > 0 ? Math.min((toNumber(actual) / f) * 100, 100) : 0
}
</script>

<template>
  <section class="section" aria-labelledby="income-title">
    <div class="section-head">
      <h2 id="income-title">Доход</h2>
      <button class="btn" type="button" :aria-expanded="showEntryForm" @click="showEntryForm = !showEntryForm">
        Записать поступление
      </button>
    </div>

    <form v-if="showEntryForm" class="inline-form" @submit.prevent="addEntry" @keydown.esc="showEntryForm = false">
      <div class="form-grid">
        <label class="field">
          Сумма, ₽
          <input v-model="entryAmount" type="number" inputmode="decimal" min="0.01" step="0.01" required autofocus />
        </label>
        <label class="field">
          Дата
          <input v-model="entryDate" type="date" required />
        </label>
      </div>
      <label class="field">
        Что пришло
        <input v-model="entryDescription" type="text" maxlength="200" placeholder="Аванс, зарплата, премия" />
      </label>
      <fieldset v-if="store.users.length > 1" class="whose">
        <legend class="field-legend">Чьи деньги</legend>
        <label v-for="user in store.users" :key="user.id" class="chip">
          <input v-model="entryUserId" type="radio" name="income-user" :value="user.id" />
          <span>{{ user.id === myId ? 'Мои' : user.display_name }}</span>
        </label>
      </fieldset>
      <div class="form-actions">
        <button class="btn btn-primary" type="submit" :disabled="submitting">Записать</button>
        <button class="btn btn-quiet" type="button" @click="showEntryForm = false">Отмена</button>
      </div>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    </form>

    <ul class="people">
      <li v-for="person in perUser" :key="person.user_id" class="person">
        <div class="line">
          <span class="name">
            <UserAvatar :user="store.userById(person.user_id)" size="md" />
            {{ person.display_name }}
          </span>
          <span class="num amount">{{ formatMoney(person.actual) }}</span>
        </div>
        <div class="bar" aria-hidden="true">
          <div class="bar-fill" :style="{ width: progress(person.actual, person.forecast) + '%' }" />
        </div>
        <div class="line sub">
          <span v-if="toNumber(person.forecast) > 0" class="muted">
            ожидается <span class="num">{{ formatMoney(person.forecast) }}</span>
          </span>
          <span v-else class="muted">ожидаемый доход не указан</span>
          <button
            v-if="person.user_id === myId && !editingForecast"
            class="btn btn-quiet small"
            type="button"
            @click="editingForecast = true"
          >
            {{ toNumber(person.forecast) > 0 ? 'Изменить' : 'Указать' }}
          </button>
        </div>
        <form
          v-if="person.user_id === myId && editingForecast"
          class="forecast-form"
          @submit.prevent="saveForecast"
          @keydown.esc="editingForecast = false"
        >
          <label class="field">
            Сколько жду в этом месяце, ₽
            <input v-model="forecastAmount" type="number" inputmode="decimal" min="0" step="0.01" autofocus />
          </label>
          <button class="btn btn-primary" type="submit">Сохранить</button>
          <button class="btn btn-quiet" type="button" @click="editingForecast = false">Отмена</button>
        </form>
      </li>
    </ul>

    <div v-if="store.incomeEntries.length" class="entries">
      <h3 class="entries-title">Поступления</h3>
      <ul class="entry-list">
        <li v-for="entry in store.incomeEntries" :key="entry.id" class="entry">
          <UserAvatar :user="store.userById(entry.user_id)" size="sm" />
          <span class="what">
            <span class="title">{{ entry.description || 'Доход' }}</span>
            <span class="meta">
              {{ formatShortDate(entry.received_date) }}<template v-if="store.users.length > 1">,
                {{ store.userName(entry.user_id) }}</template>
            </span>
          </span>
          <span class="num amount">{{ formatMoney(entry.amount) }}</span>
          <ConfirmButton icon class="remove" confirm-label="Удалить поступление" @confirm="store.removeIncomeEntry(entry.id)" />
        </li>
      </ul>
    </div>
    <p v-else class="empty">
      Пока ничего не пришло. Когда придёт аванс или зарплата, запишите поступление.
    </p>
  </section>
</template>

<style scoped>
.section {
  gap: 0.75rem;
}

.inline-form {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--ink-wash);
  border-radius: 10px;
}

.whose {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
  padding: 0;
  border: none;
}

.field-legend {
  float: left;
  margin-right: 0.5rem;
  font-size: 0.875rem;
  color: var(--muted);
}

.form-actions {
  display: flex;
  gap: 0.25rem;
}

.people {
  list-style: none;
  margin: 0;
  padding: 0;
}

.person {
  padding: 0.75rem 0 0.4rem;
  border-bottom: 1px solid var(--line);
}

.line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.name {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  font-weight: 600;
}

.amount {
  font-weight: 600;
}

.sub {
  align-items: center;
  font-size: 0.875rem;
  min-height: 2rem;
}

.small {
  min-height: 1.75rem;
  padding: 0.1rem 0.5rem;
  font-size: 0.875rem;
  margin-right: -0.5rem;
}

.bar {
  margin: 0.4rem 0 0.1rem;
  height: 4px;
  border-radius: 2px;
  background: var(--line);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: var(--ink);
  transition: width 0.4s ease;
}

.forecast-form {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.5rem;
  padding: 0.75rem;
  margin: 0.25rem 0 0.5rem;
  background: var(--ink-wash);
  border-radius: 10px;
}

.forecast-form .field {
  flex: 1 1 12rem;
}

.entries-title {
  font-size: 0.95rem;
  padding-bottom: 0.4rem;
}

.entry-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.entry {
  display: grid;
  grid-template-columns: 1.6rem minmax(0, 1fr) auto 2rem;
  column-gap: 0.75rem;
  align-items: center;
  gap: 0.75rem;
  padding: 0.4rem 0;
  border-bottom: 1px dashed var(--line);
  font-size: 0.95rem;
}

.entry:last-child {
  border-bottom: none;
}

.date {
  font-size: 0.875rem;
}

.what {
  overflow-wrap: anywhere;
}

.who {
  margin-left: 0.4rem;
  font-size: 0.875rem;
  font-style: italic;
}
</style>
