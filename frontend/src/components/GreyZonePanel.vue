<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useBudgetStore } from '../stores/budget'
import { formatMoney, formatShortDate, todayIso, toNumber } from '../utils/format'
import ConfirmButton from './ConfirmButton.vue'
import UserAvatar from './UserAvatar.vue'

const auth = useAuthStore()
const store = useBudgetStore()

const myId = computed(() => auth.user?.id ?? null)
const perUser = computed(() => store.summary?.grey_zone.per_user ?? [])
const me = computed(() => perUser.value.find((u) => u.user_id === myId.value) ?? null)

const mode = ref<'none' | 'take' | 'limit'>('none')
const amount = ref('')
const takenDate = ref(todayIso())
const error = ref('')
const submitting = ref(false)

watch(mode, (value) => {
  error.value = ''
  if (value === 'limit') amount.value = toNumber(me.value?.limit) ? String(toNumber(me.value?.limit)) : ''
  if (value === 'take') amount.value = ''
})

async function submit() {
  if (!amount.value && mode.value === 'take') return
  submitting.value = true
  error.value = ''
  try {
    if (mode.value === 'take') {
      await store.takeFromGreyZone(String(amount.value), takenDate.value)
    } else {
      await store.setMyGreyZoneLimit(String(amount.value || '0'))
    }
    mode.value = 'none'
  } catch {
    error.value = 'Не сохранилось. Попробуйте ещё раз.'
  } finally {
    submitting.value = false
  }
}

function usedPercent(taken: string, limit: string): number {
  const l = toNumber(limit)
  return l > 0 ? Math.min((toNumber(taken) / l) * 100, 100) : 0
}
</script>

<template>
  <section class="section" aria-labelledby="grey-title">
    <div class="section-head">
      <h2 id="grey-title">Серая зона</h2>
      <div v-if="mode === 'none'" class="head-actions">
        <button class="btn btn-quiet" type="button" @click="mode = 'limit'">Мой лимит</button>
        <button class="btn" type="button" @click="mode = 'take'">Взять себе</button>
      </div>
    </div>
    <p class="hint muted">Личные деньги каждого. Здесь видно, кто сколько взял, но не на что потратил.</p>

    <form v-if="mode !== 'none'" class="inline-form" @submit.prevent="submit" @keydown.esc="mode = 'none'">
      <div class="form-grid">
        <label class="field">
          {{ mode === 'take' ? 'Сколько беру, ₽' : 'Мой лимит на месяц, ₽' }}
          <input
            v-model="amount"
            type="number"
            inputmode="decimal"
            :min="mode === 'take' ? 0.01 : 0"
            step="0.01"
            :required="mode === 'take'"
            autofocus
          />
        </label>
        <label v-if="mode === 'take'" class="field">
          Дата
          <input v-model="takenDate" type="date" required />
        </label>
      </div>
      <p v-if="mode === 'take' && me && toNumber(me.limit) > 0" class="muted small-text">
        Осталось в лимите <span class="num">{{ formatMoney(me.remaining) }}</span>
      </p>
      <div class="form-actions">
        <button class="btn btn-primary" type="submit" :disabled="submitting">
          {{ mode === 'take' ? 'Взять' : 'Сохранить' }}
        </button>
        <button class="btn btn-quiet" type="button" @click="mode = 'none'">Отмена</button>
      </div>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    </form>

    <ul class="people">
      <li v-for="person in perUser" :key="person.user_id" class="person" :class="{ over: toNumber(person.remaining) < 0 }">
        <div class="line">
          <span class="name">
            <UserAvatar :user="store.userById(person.user_id)" size="md" />
            {{ person.display_name }}
          </span>
          <span>
            <span class="num taken">{{ formatMoney(person.taken) }}</span>
            <span v-if="toNumber(person.limit) > 0" class="muted"> из <span class="num">{{ formatMoney(person.limit) }}</span></span>
          </span>
        </div>
        <div v-if="toNumber(person.limit) > 0" class="bar" aria-hidden="true">
          <div class="bar-fill" :style="{ width: usedPercent(person.taken, person.limit) + '%' }" />
        </div>
        <p v-else class="muted small-text">лимит не задан</p>
      </li>
    </ul>

    <ul v-if="store.greyZone.entries.length" class="entry-list">
      <li v-for="entry in store.greyZone.entries" :key="entry.id" class="entry">
        <UserAvatar :user="store.userById(entry.user_id)" size="sm" />
        <span class="what">
          <span class="title">{{ entry.user_id === myId ? 'Вы' : store.userName(entry.user_id) }}</span>
          <span class="meta">{{ formatShortDate(entry.taken_date) }}</span>
        </span>
        <span class="num amount">{{ formatMoney(entry.amount) }}</span>
        <ConfirmButton
          v-if="entry.user_id === myId"
          icon
          class="remove"
          confirm-label="Удалить запись"
          @confirm="store.removeGreyZoneEntry(entry.id)"
        />
        <span v-else class="remove-placeholder" />
      </li>
    </ul>
  </section>
</template>

<style scoped>
.section {
  gap: 0.75rem;
}

.head-actions {
  display: flex;
  gap: 0.25rem;
}

.hint {
  font-size: 0.9rem;
  max-width: 36rem;
}

.inline-form {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--ink-wash);
  border-radius: 10px;
}

.form-actions {
  display: flex;
  gap: 0.25rem;
}

.small-text {
  font-size: 0.875rem;
}

.people {
  list-style: none;
  margin: 0;
  padding: 0;
}

.person {
  padding: 0.7rem 0 0.6rem;
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

.taken {
  font-weight: 600;
}

.over .taken {
  color: var(--red);
}

.bar {
  margin-top: 0.45rem;
  height: 4px;
  border-radius: 2px;
  background: var(--line);
  overflow: hidden;
}

/* Muted graphite rather than ink: this is money that leaves the shared ledger. */
.bar-fill {
  height: 100%;
  background: var(--muted);
  transition: width 0.4s ease;
}

.over .bar-fill {
  background: var(--red);
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
  padding: 0.35rem 0;
  border-bottom: 1px dashed var(--line);
  font-size: 0.95rem;
}

.entry:last-child {
  border-bottom: none;
}

.date {
  font-size: 0.875rem;
}

.amount {
  font-weight: 600;
}
</style>
