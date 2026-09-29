import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useMonthsStore } from '../stores/months'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'home',
      // Lands on the current calendar month's dashboard if it already exists,
      // otherwise falls back to History where the couple can create it.
      component: () => import('../views/HistoryView.vue'),
      beforeEnter: async () => {
        const months = useMonthsStore()
        if (!months.loaded) {
          await months.loadMonths()
        }
        const now = new Date()
        const year = now.getFullYear()
        const month = now.getMonth() + 1
        const current = months.months.find((m) => m.year === year && m.month === month)
        if (current) {
          return { name: 'dashboard', params: { year, month } }
        }
        return { name: 'history' }
      },
    },
    {
      path: '/months/:year/:month',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      props: true,
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('../views/HistoryView.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  // The router starts its first navigation as soon as it is installed, which can
  // be before main.ts's session check finishes — wait for it here.
  if (!auth.isReady) {
    await auth.loadCurrentUser()
  }
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'home' }
  }
  return true
})

export default router
