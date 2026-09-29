<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { createTelegramLinkCode, unlinkTelegram } from '../api/users'
import { useAuthStore } from '../stores/auth'
import type { TelegramLinkCode, User } from '../types/models'

// Linking this person's Telegram to the bot: a one-time code, written like a note on a
// scrap of squared paper, that they send to the bot as /link CODE.
const emit = defineEmits<{ changed: [user: User] }>()
const auth = useAuthStore()

const linked = computed(() => auth.user?.telegram_linked ?? false)
const code = ref<TelegramLinkCode | null>(null)
const busy = ref(false)
const error = ref('')
const copied = ref(false)
const now = ref(Date.now())
const timer = window.setInterval(() => (now.value = Date.now()), 15_000)
onBeforeUnmount(() => window.clearInterval(timer))

const expired = computed(() => (code.value ? new Date(code.value.expires_at).getTime() <= now.value : false))
const until = computed(() =>
  code.value
    ? new Intl.DateTimeFormat('ru-RU', { hour: '2-digit', minute: '2-digit' }).format(new Date(code.value.expires_at))
    : '',
)
const command = computed(() => (code.value ? `/link ${code.value.code}` : ''))
const deepLink = computed(() =>
  code.value?.bot_username ? `https://t.me/${code.value.bot_username}?start=${code.value.code}` : null,
)

async function getCode() {
  busy.value = true
  error.value = ''
  copied.value = false
  try {
    code.value = await createTelegramLinkCode()
    now.value = Date.now()
  } catch {
    error.value = 'Код не получился. Попробуйте ещё раз.'
  } finally {
    busy.value = false
  }
}

async function copyCommand() {
  try {
    await navigator.clipboard.writeText(command.value)
    copied.value = true
  } catch {
    copied.value = false
  }
}

async function unlink() {
  busy.value = true
  try {
    emit('changed', await unlinkTelegram())
    code.value = null
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="section" aria-labelledby="telegram-title">
    <div class="section-head">
      <h2 id="telegram-title">Telegram</h2>
    </div>

    <template v-if="linked">
      <p class="status">
        <svg viewBox="0 0 16 16" aria-hidden="true"><path d="m3 8.5 3 3 7-7" /></svg>
        Telegram привязан. В общей беседе бот записывает ваши траты и отвечает на команды.
      </p>
      <div>
        <button class="btn btn-quiet" type="button" :disabled="busy" @click="unlink">Отвязать</button>
      </div>
    </template>

    <template v-else>
      <p class="muted intro">
        Бот в общей беседе записывает траты одной строкой, например «450 прод пятёрочка», и показывает остатки.
        Чтобы он узнавал вас, привяжите Telegram.
      </p>

      <div v-if="code && !expired" class="code-block">
        <p class="scrap grid-paper hand num" aria-label="Код привязки">{{ code.code }}</p>
        <div class="steps">
          <p>Отправьте боту в беседе или в личке:</p>
          <p class="command-line">
            <code>{{ command }}</code>
            <button class="btn btn-quiet small" type="button" @click="copyCommand">
              {{ copied ? 'Скопировано' : 'Скопировать' }}
            </button>
          </p>
          <a v-if="deepLink" class="btn btn-primary" :href="deepLink" target="_blank" rel="noopener">
            Открыть бота и привязать
          </a>
          <p class="muted small-text">Код одноразовый и действует до {{ until }}.</p>
        </div>
      </div>

      <div v-else>
        <p v-if="code && expired" class="muted small-text">Код устарел, получите новый.</p>
        <button class="btn btn-primary" type="button" :disabled="busy" @click="getCode">Получить код</button>
      </div>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    </template>
  </section>
</template>

<style scoped>
.status {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.status svg {
  flex: none;
  width: 1.1rem;
  height: 1.1rem;
  margin-top: 0.2rem;
  fill: none;
  stroke: var(--green);
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.intro {
  max-width: 34rem;
}

.code-block {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem 1.5rem;
}

/* The code, handwritten on a scrap torn from the notebook. */
.scrap {
  flex: none;
  padding: 0.35rem 1.1rem 0.25rem;
  border: 1px solid var(--line);
  border-radius: 4px 10px 6px 12px;
  font-size: 2.75rem;
  letter-spacing: 0.08em;
  transform: rotate(-1.5deg);
  animation: write-in 0.8s cubic-bezier(0.55, 0, 0.3, 1) both;
}

.steps {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
  min-width: 0;
}

.command-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem 0.5rem;
}

code {
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  background: var(--ink-wash);
  color: var(--ink);
  font-size: 1rem;
}

.small {
  min-height: 2rem;
  padding: 0.2rem 0.6rem;
  font-size: 0.875rem;
}

.small-text {
  font-size: 0.85rem;
}
</style>
