import { defineStore } from 'pinia'
import { fetchMe, login as apiLogin, logout as apiLogout } from '../api/auth'
import type { LoginRequest, User } from '../types/models'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    // Distinguishes "haven't checked yet" from "checked, not logged in" so the
    // router guard doesn't redirect to /login before the initial fetchMe() resolves.
    isReady: false,
  }),
  getters: {
    isAuthenticated: (state) => state.user !== null,
  },
  actions: {
    async login(payload: LoginRequest) {
      this.user = await apiLogin(payload)
    },
    setUser(user: User) {
      this.user = user
    },
    async logout() {
      await apiLogout()
      this.user = null
    },
    async loadCurrentUser() {
      try {
        this.user = await fetchMe()
      } catch {
        this.user = null
      } finally {
        this.isReady = true
      }
    },
  },
})
