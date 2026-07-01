/**
 * Pinia store for portfolio state management.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import portfolioApi from '@/services/portfolioApi'

export const usePortfolioStore = defineStore('portfolio', () => {
  // ── State ──────────────────────────────────────────────

  const portfolios = ref([])
  const currentPortfolio = ref(null)
  const holdings = ref([])
  const performance = ref([])
  const allocation = ref([])
  const summary = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // ── Getters ────────────────────────────────────────────

  const portfolioCount = computed(() => portfolios.value.length)
  const totalValue = computed(() => {
    return portfolios.value.reduce((sum, p) => sum + Number(p.total_value || 0), 0)
  })
  const totalPnl = computed(() => {
    return portfolios.value.reduce((sum, p) => sum + Number(p.total_pnl || 0), 0)
  })

  // ── Actions ────────────────────────────────────────────

  async function fetchSummary() {
    try {
      const res = await portfolioApi.summary()
      summary.value = res.data
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load summary'
      throw e
    }
  }

  async function fetchPortfolios() {
    loading.value = true
    error.value = null
    try {
      const res = await portfolioApi.list()
      portfolios.value = res.data
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load portfolios'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createPortfolio(data) {
    loading.value = true
    error.value = null
    try {
      const res = await portfolioApi.create(data)
      portfolios.value.unshift(res.data)
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to create portfolio'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updatePortfolio(id, data) {
    loading.value = true
    error.value = null
    try {
      const res = await portfolioApi.update(id, data)
      const idx = portfolios.value.findIndex((p) => p.id === id)
      if (idx !== -1) portfolios.value[idx] = res.data
      if (currentPortfolio.value?.id === id) currentPortfolio.value = res.data
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to update portfolio'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deletePortfolio(id) {
    loading.value = true
    error.value = null
    try {
      await portfolioApi.delete(id)
      portfolios.value = portfolios.value.filter((p) => p.id !== id)
      if (currentPortfolio.value?.id === id) currentPortfolio.value = null
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to delete portfolio'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchPortfolio(id) {
    loading.value = true
    error.value = null
    try {
      const res = await portfolioApi.get(id)
      currentPortfolio.value = res.data
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load portfolio'
      throw e
    } finally {
      loading.value = false
    }
  }

  // ── Holdings Actions ──────────────────────────────────

  async function fetchHoldings(portfolioId) {
    try {
      const res = await portfolioApi.listHoldings(portfolioId)
      holdings.value = res.data
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load holdings'
      throw e
    }
  }

  async function addHolding(portfolioId, data) {
    try {
      const res = await portfolioApi.addHolding(portfolioId, data)
      holdings.value.push(res.data)
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to add holding'
      throw e
    }
  }

  async function updateHolding(portfolioId, holdingId, data) {
    try {
      const res = await portfolioApi.updateHolding(portfolioId, holdingId, data)
      const idx = holdings.value.findIndex((h) => h.id === holdingId)
      if (idx !== -1) holdings.value[idx] = res.data
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to update holding'
      throw e
    }
  }

  async function removeHolding(portfolioId, holdingId) {
    try {
      await portfolioApi.removeHolding(portfolioId, holdingId)
      holdings.value = holdings.value.filter((h) => h.id !== holdingId)
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to remove holding'
      throw e
    }
  }

  // ── Rebalance Actions ─────────────────────────────────

  async function rebalancePlan(portfolioId) {
    try {
      const res = await portfolioApi.rebalancePlan(portfolioId)
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to calculate rebalance plan'
      throw e
    }
  }

  async function rebalanceExecute(portfolioId, data) {
    try {
      const res = await portfolioApi.rebalanceExecute(portfolioId, data)
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to execute rebalance'
      throw e
    }
  }

  // ── Performance & Allocation ──────────────────────────

  async function fetchPerformance(portfolioId, days = 30) {
    try {
      const res = await portfolioApi.performance(portfolioId, days)
      performance.value = res.data
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load performance'
      throw e
    }
  }

  async function fetchAllocation(portfolioId) {
    try {
      const res = await portfolioApi.allocation(portfolioId)
      allocation.value = res.data
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load allocation'
      throw e
    }
  }

  // ── Orders ────────────────────────────────────────────────

  const orders = ref([])

  async function fetchOrders(portfolioId) {
    try {
      const res = await portfolioApi.orders(portfolioId)
      orders.value = res.data
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load orders'
      throw e
    }
  }

  async function syncPortfolio(portfolioId) {
    try {
      const res = await portfolioApi.sync(portfolioId)
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to sync portfolio'
      throw e
    }
  }

  // ── Bulk Order Actions ─────────────────────────────────

  async function bulkCancelOrders(portfolioId, orderIds) {
    try {
      const res = await portfolioApi.bulkCancelOrders(portfolioId, orderIds)
      // Refresh orders
      await fetchOrders(portfolioId)
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to cancel orders'
      throw e
    }
  }

  async function replaceOrder(portfolioId, orderId, data) {
    try {
      const res = await portfolioApi.replaceOrder(portfolioId, orderId, data)
      // Refresh orders
      await fetchOrders(portfolioId)
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to replace order'
      throw e
    }
  }

  async function bulkDeleteOrders(portfolioId, orderIds) {
    try {
      const res = await portfolioApi.bulkDeleteOrders(portfolioId, orderIds)
      // Refresh orders
      await fetchOrders(portfolioId)
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to delete orders'
      throw e
    }
  }

  // ── Broker Orders & Trades ─────────────────────────────

  const brokerOrders = ref([])
  const brokerTrades = ref([])

  async function fetchBrokerOrders(portfolioId) {
    try {
      const res = await portfolioApi.brokerOrders(portfolioId)
      brokerOrders.value = res.data || []
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load broker orders'
      brokerOrders.value = []
      return []
    }
  }

  async function fetchBrokerTrades(portfolioId) {
    try {
      const res = await portfolioApi.brokerTrades(portfolioId)
      brokerTrades.value = res.data || []
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load broker trades'
      brokerTrades.value = []
      return []
    }
  }

  return {
    portfolios,
    currentPortfolio,
    holdings,
    performance,
    allocation,
    summary,
    loading,
    error,
    portfolioCount,
    totalValue,
    totalPnl,
    fetchSummary,
    fetchPortfolios,
    createPortfolio,
    updatePortfolio,
    deletePortfolio,
    fetchPortfolio,
    fetchHoldings,
    addHolding,
    updateHolding,
    removeHolding,
    rebalancePlan,
    rebalanceExecute,
    fetchPerformance,
    fetchAllocation,
    fetchOrders,
    syncPortfolio,
    orders,
    bulkCancelOrders,
    replaceOrder,
    bulkDeleteOrders,
    brokerOrders,
    brokerTrades,
    fetchBrokerOrders,
    fetchBrokerTrades,
  }
})
