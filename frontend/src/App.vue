<script setup lang="ts">
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="app-shell">
    <header v-if="auth.isAuthenticated" class="app-header">
      <RouterLink to="/" class="wordmark hand" aria-label="Niksi, на главную">Niksi</RouterLink>
      <nav class="app-nav">
        <RouterLink to="/history" class="nav-link">Все месяцы</RouterLink>
        <span class="app-user">{{ auth.user?.display_name }}</span>
        <button type="button" class="btn btn-quiet" @click="handleLogout">Выйти</button>
      </nav>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.5rem 0.5rem;
}

.wordmark {
  font-size: 2.25rem;
  text-decoration: none;
}

.app-nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.nav-link {
  color: var(--text);
  text-decoration: none;
  font-weight: 500;
  padding: 0.4rem 0.6rem;
  border-radius: var(--radius-control);
}

.nav-link:hover,
.nav-link.router-link-active {
  color: var(--ink);
  background: var(--ink-wash);
}

.app-user {
  color: var(--muted);
  padding-left: 0.75rem;
  border-left: 1px solid var(--line);
}

.app-main {
  flex: 1;
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  padding: 1rem 1.5rem 4rem;
}

@media (max-width: 560px) {
  .app-header {
    padding-inline: 1rem;
  }

  .app-main {
    padding-inline: 1rem;
  }

  .app-user {
    display: none;
  }
}
</style>
