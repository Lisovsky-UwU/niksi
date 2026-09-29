import { defineStore } from 'pinia'
import {
  createReconciliation as apiCreateReconciliation,
  deleteReconciliation as apiDeleteReconciliation,
  getBalance,
  listReconciliations,
} from '../api/balance'
import {
  addTransfer as apiAddTransfer,
  createPot as apiCreatePot,
  deletePot as apiDeletePot,
  deleteTransfer as apiDeleteTransfer,
  listPots,
  listTransfers,
  updatePot as apiUpdatePot,
} from '../api/savings'
import type {
  BalanceStatus,
  Reconciliation,
  ReconciliationCreateRequest,
  SavingsPot,
  SavingsPotCreateRequest,
  SavingsPotUpdateRequest,
  SavingsTransfer,
  SavingsTransferCreateRequest,
} from '../types/models'

// Money that lives outside a single month: the reconciliation baseline and the savings pots.
export const useMoneyStore = defineStore('money', {
  state: () => ({
    balance: null as BalanceStatus | null,
    reconciliations: [] as Reconciliation[],
    pots: [] as SavingsPot[],
    transfers: {} as Record<number, SavingsTransfer[]>,
    showArchived: false,
    loaded: false,
  }),
  actions: {
    async load() {
      const [balance, reconciliations, pots] = await Promise.all([
        getBalance(),
        listReconciliations(),
        listPots(this.showArchived),
      ])
      this.balance = balance
      this.reconciliations = reconciliations
      this.pots = pots
      this.loaded = true
    },

    async refreshBalance() {
      this.balance = await getBalance()
    },

    async reconcile(payload: ReconciliationCreateRequest) {
      const created = await apiCreateReconciliation(payload)
      this.reconciliations = [created, ...this.reconciliations]
      await this.refreshBalance()
      return created
    },

    async undoReconciliation(id: number) {
      await apiDeleteReconciliation(id)
      this.reconciliations = this.reconciliations.filter((r) => r.id !== id)
      await this.refreshBalance()
    },

    async setShowArchived(value: boolean) {
      this.showArchived = value
      this.pots = await listPots(value)
    },

    async createPot(payload: SavingsPotCreateRequest) {
      const pot = await apiCreatePot(payload)
      this.pots = [...this.pots, pot]
    },

    async updatePot(potId: number, payload: SavingsPotUpdateRequest) {
      const pot = await apiUpdatePot(potId, payload)
      this.pots = this.showArchived || !pot.is_archived
        ? this.pots.map((p) => (p.id === potId ? pot : p))
        : this.pots.filter((p) => p.id !== potId)
    },

    async deletePot(potId: number) {
      await apiDeletePot(potId)
      this.pots = this.pots.filter((p) => p.id !== potId)
    },

    async loadTransfers(potId: number) {
      this.transfers[potId] = await listTransfers(potId)
    },

    async addTransfer(potId: number, payload: SavingsTransferCreateRequest) {
      const transfer = await apiAddTransfer(potId, payload)
      if (this.transfers[potId]) {
        this.transfers[potId] = [transfer, ...this.transfers[potId]]
      }
      await this.refreshPots()
      await this.refreshBalance()
    },

    async deleteTransfer(potId: number, transferId: number) {
      await apiDeleteTransfer(transferId)
      if (this.transfers[potId]) {
        this.transfers[potId] = this.transfers[potId].filter((t) => t.id !== transferId)
      }
      await this.refreshPots()
      await this.refreshBalance()
    },

    async refreshPots() {
      this.pots = await listPots(this.showArchived)
    },
  },
})
