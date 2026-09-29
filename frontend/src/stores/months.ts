import { defineStore } from 'pinia'
import { createMonth as apiCreateMonth, listMonths, setMonthStart as apiSetMonthStart } from '../api/months'
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
      // A new month closes the previous one's period, so reload everyone's end dates.
      await this.loadMonths()
      return month
    },
    /** Moving a start also moves the previous month's end, so the whole list is reloaded. */
    async setStart(monthId: number, startDate: string) {
      const month = await apiSetMonthStart(monthId, startDate)
      await this.loadMonths()
      return month
    },
  },
})
