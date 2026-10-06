import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useMonthsStore } from '../stores/months'
import { currentMonth } from '../utils/periods'

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
      // Lands on the month whose budget period is running now if it exists,
      // otherwise falls back to History where the couple can create it.
      component: () => import('../views/HistoryView.vue'),
      beforeEnter: async () => {
        const months = useMonthsStore()
        if (!months.loaded) {
          await months.loadMonths()
        }
        // The month whose budget period today falls into, not the calendar month.
        const current = currentMonth(months.months)
        if (current) {
          return { name: 'dashboard', params: { year: current.year, month: current.month } }
        }
        return { name: 'history' }
      },
    },
    {
      path: '/months/:year/:month',
      component: () => import('../views/DashboardView.vue'),
      props: true,
      children: [
        { path: '', name: 'dashboard', component: () => import('../views/MonthOverview.vue') },
        { path: 'categories', name: 'month-categories', component: () => import('../components/CategoryList.vue') },
        {
          path: 'expenses',
          name: 'month-expenses',
          component: () => import('../components/ExpenseList.vue'),
          props: { limit: 15, filterable: true },
        },
        { path: 'income', name: 'month-income', component: () => import('../components/IncomePanel.vue') },
        { path: 'grey-zone', name: 'month-grey-zone', component: () => import('../components/GreyZonePanel.vue') },
      ],
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('../views/HistoryView.vue'),
    },
    {
      path: '/money',
      component: () => import('../views/MoneyView.vue'),
      children: [
        { path: '', name: 'money', component: () => import('../views/MoneyReconcile.vue') },
        { path: 'savings', name: 'money-savings', component: () => import('../components/SavingsSection.vue') },
        { path: 'archive', name: 'money-archive', component: () => import('../components/SavingsArchive.vue') },
        { path: 'loans', name: 'money-loans', component: () => import('../components/LoansSection.vue') },
        {
          path: 'loans/:loanId',
          name: 'money-loan',
          component: () => import('../views/LoanView.vue'),
          props: true,
        },
        {
          path: 'pots/:potId',
          name: 'money-pot',
          component: () => import('../views/SavingsPotView.vue'),
          props: true,
        },
      ],
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
