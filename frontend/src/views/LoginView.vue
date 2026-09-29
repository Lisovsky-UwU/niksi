<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login({ email: email.value, password: password.value })
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.push(redirect)
  } catch {
    error.value = 'Email или пароль не подошли. Проверьте раскладку и попробуйте ещё раз.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page grid-paper">
    <form class="login" @submit.prevent="handleSubmit">
      <h1 class="wordmark hand">Niksi</h1>
      <p class="tagline">Общий бюджет на двоих</p>

      <label class="field">
        Email
        <input v-model="email" type="email" required autocomplete="username" autofocus />
      </label>
      <label class="field">
        Пароль
        <input v-model="password" type="password" required autocomplete="current-password" />
      </label>

      <p v-if="error" class="error-text" role="alert">{{ error }}</p>

      <button class="btn btn-primary submit" type="submit" :disabled="loading">
        {{ loading ? 'Входим…' : 'Войти' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.login-page {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1rem;
  overflow-y: auto;
}

/* Margin line running the full height of the page, as on a notebook sheet. */
.login-page::before {
  content: '';
  position: fixed;
  top: 0;
  bottom: 0;
  left: calc(var(--cell) * 4);
  width: 2px;
  background: var(--margin);
}

.login {
  position: relative;
  width: 100%;
  max-width: 22rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 2rem 1.75rem 1.75rem;
  background: var(--sheet);
  border: 1px solid var(--line);
  border-radius: var(--radius-sheet);
}

.wordmark {
  font-size: 4.5rem;
  margin: -0.5rem 0 -0.5rem -0.1rem;
  animation: write-in 0.9s cubic-bezier(0.55, 0, 0.3, 1) both;
}

@keyframes write-in {
  from {
    clip-path: inset(-20% 100% -20% 0);
  }
  to {
    clip-path: inset(-20% -5% -20% 0);
  }
}

.tagline {
  color: var(--muted);
  margin-bottom: 0.5rem;
}

.submit {
  margin-top: 0.25rem;
  min-height: 2.75rem;
}

@media (max-width: 560px) {
  .login-page::before {
    left: var(--cell);
  }
}
</style>
