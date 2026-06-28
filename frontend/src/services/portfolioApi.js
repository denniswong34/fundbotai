/**
 * Portfolio API service — wraps all portfolio and holding endpoints.
 */

import client from '@/api/client'

export default {
  // ── Portfolio CRUD ──────────────────────────────────────

  list() {
    return client.get('/portfolios')
  },

  create(data) {
    return client.post('/portfolios', data)
  },

  get(id) {
    return client.get(`/portfolios/${id}`)
  },

  update(id, data) {
    return client.put(`/portfolios/${id}`, data)
  },

  delete(id) {
    return client.delete(`/portfolios/${id}`)
  },

  summary() {
    return client.get('/portfolios/summary')
  },

  // ── Holdings ───────────────────────────────────────────

  listHoldings(portfolioId) {
    return client.get(`/portfolios/${portfolioId}/holdings`)
  },

  addHolding(portfolioId, data) {
    return client.post(`/portfolios/${portfolioId}/holdings`, data)
  },

  updateHolding(portfolioId, holdingId, data) {
    return client.put(`/portfolios/${portfolioId}/holdings/${holdingId}`, data)
  },

  removeHolding(portfolioId, holdingId) {
    return client.delete(`/portfolios/${portfolioId}/holdings/${holdingId}`)
  },

  batchHoldings(portfolioId, holdings) {
    return client.put(`/portfolios/${portfolioId}/holdings/batch`, holdings)
  },

  // ── Rebalance ─────────────────────────────────────────

  rebalancePlan(portfolioId) {
    return client.post(`/portfolios/${portfolioId}/rebalance/plan`)
  },

  rebalanceExecute(portfolioId, data) {
    return client.post(`/portfolios/${portfolioId}/rebalance/execute`, data)
  },

  // ── Sync ──────────────────────────────────────────────

  sync(portfolioId) {
    return client.post(`/portfolios/${portfolioId}/sync`)
  },

  // ── Performance & Allocation ──────────────────────────

  performance(portfolioId, days = 30) {
    return client.get(`/portfolios/${portfolioId}/performance`, { params: { days } })
  },

  allocation(portfolioId) {
    return client.get(`/portfolios/${portfolioId}/allocation`)
  },
}
