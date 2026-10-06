import { defineStore } from 'pinia'
import {
  createReconciliation as apiCreateReconciliation,
  deleteReconciliation as apiDeleteReconciliation,
  getBalance,
  listReconciliations,
} from '../api/balance'
import {
  addPayment as apiAddPayment,
  createLoan as apiCreateLoan,
  deleteLoan as apiDeleteLoan,
  deletePayment as apiDeletePayment,
  listLoans,
  listPayments,
  updateLoan as apiUpdateLoan,
} from '../api/loans'
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
  Loan,
  LoanCreateRequest,
  LoanPayment,
  LoanPaymentCreateRequest,
  LoanUpdateRequest,
  Reconciliation,
  ReconciliationCreateRequest,
  SavingsPot,
  SavingsPotCreateRequest,
  SavingsPotUpdateRequest,
  SavingsTransfer,
  SavingsTransferCreateRequest,
} from '../types/models'

// Money that lives outside a single month: the reconciliation baseline, the savings pots and the loans.
export const useMoneyStore = defineStore('money', {
  state: () => ({
    balance: null as BalanceStatus | null,
    reconciliations: [] as Reconciliation[],
    /** Every pot, current and archived; the tabs pick theirs through the getters. */
    pots: [] as SavingsPot[],
    transfers: {} as Record<number, SavingsTransfer[]>,
    /** Open loans first, then closed ones, as the API returns them. */
    loans: [] as Loan[],
    loanPayments: {} as Record<number, LoanPayment[]>,
    loaded: false,
  }),
  getters: {
    activePots: (state) => state.pots.filter((p) => !p.is_archived),
    archivedPots: (state) => state.pots.filter((p) => p.is_archived),
    openLoans: (state) => state.loans.filter((l) => !l.is_closed),
    closedLoans: (state) => state.loans.filter((l) => l.is_closed),
  },
  actions: {
    async load() {
      const [balance, reconciliations, pots, loans] = await Promise.all([
        getBalance(),
        listReconciliations(),
        listPots(true),
        listLoans(),
      ])
      this.balance = balance
      this.reconciliations = reconciliations
      this.pots = pots
      this.loans = loans
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

    async createPot(payload: SavingsPotCreateRequest) {
      const pot = await apiCreatePot(payload)
      this.pots = [...this.pots, pot]
    },

    async updatePot(potId: number, payload: SavingsPotUpdateRequest) {
      const pot = await apiUpdatePot(potId, payload)
      this.pots = this.pots.map((p) => (p.id === potId ? pot : p))
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
      this.pots = await listPots(true)
    },

    async createLoan(payload: LoanCreateRequest) {
      const loan = await apiCreateLoan(payload)
      await this.refreshLoans()
      return loan
    },

    async updateLoan(loanId: number, payload: LoanUpdateRequest) {
      await apiUpdateLoan(loanId, payload)
      await this.refreshLoans()
    },

    async deleteLoan(loanId: number) {
      await apiDeleteLoan(loanId)
      this.loans = this.loans.filter((l) => l.id !== loanId)
    },

    async loadLoanPayments(loanId: number) {
      this.loanPayments[loanId] = await listPayments(loanId)
    },

    async addLoanPayment(loanId: number, payload: LoanPaymentCreateRequest) {
      const payment = await apiAddPayment(loanId, payload)
      await Promise.all([this.loadLoanPayments(loanId), this.refreshLoans(), this.refreshBalance()])
      return payment
    },

    async deleteLoanPayment(loanId: number, paymentId: number) {
      await apiDeletePayment(paymentId)
      await Promise.all([this.loadLoanPayments(loanId), this.refreshLoans(), this.refreshBalance()])
    },

    async refreshLoans() {
      this.loans = await listLoans()
    },
  },
})
