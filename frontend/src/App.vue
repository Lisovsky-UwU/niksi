<script setup lang="ts">
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

async function handleLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="app-shell">
    <header v-if="auth.isAuthenticated" class="app-header">
      <RouterLink to="/" class="wordmark hand" aria-label="Niksi, на главную">Niksi</RouterLink>
      <nav class="app-nav" aria-label="Разделы">
        <!-- "/" redirects to the current month, so highlight it on any month page and tab. -->
        <RouterLink
          to="/"
          class="nav-link"
          :class="{ 'router-link-active': route.path.startsWith('/months/') }"
          :aria-current="route.path.startsWith('/months/') ? 'page' : undefined"
        >
          Месяц
        </RouterLink>
        <RouterLink to="/money" class="nav-link">Деньги</RouterLink>
        <RouterLink to="/history" class="nav-link">Все месяцы</RouterLink>
      </nav>
      <div class="app-account">
        <span class="app-user">{{ auth.user?.display_name }}</span>
        <button type="button" class="btn btn-quiet" @click="handleLogout">Выйти</button>
      </div>
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
  gap: 0.25rem;
  margin-right: auto;
  margin-left: 1rem;
}

.app-account {
  display: flex;
  align-items: center;
  gap: 0.25rem;
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

@media (max-width: 640px) {
  .app-header {
    flex-wrap: wrap;
    padding-inline: 1rem;
    row-gap: 0.25rem;
  }

  /* Sections go on their own row under the wordmark. */
  .app-nav {
    order: 3;
    flex-basis: 100%;
    margin: 0 0 0 -0.6rem;
  }
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
