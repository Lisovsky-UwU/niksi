import { defineStore } from 'pinia'
import { createMonth as apiCreateMonth, listMonths } from '../api/months'
import type { Month, MonthCreateRequest } from '../types/models'

export const useMonthsStore = defineStore('months', {
  state: () => ({
    months: [] as Month[],
    loaded: false,
  }),
  actions: {
    async loadMonths() {
      this.months = await listMonths()
      this.loaded = true
    },
    async createMonth(payload: MonthCreateRequest) {
      const month = await apiCreateMonth(payload)
      this.months = [month, ...this.months]
      return month
    },
  },
})
