/**
 * Arena API service — AI manager management, decision triggering, leaderboard.
 */

import client from '@/api/client'

export default {
  // ── AI Manager CRUD ──────────────────────────────────────

  list() {
    return client.get('/ai-managers')
  },

  create(data) {
    return client.post('/ai-managers', data)
  },

  get(id) {
    return client.get(`/ai-managers/${id}`)
  },

  update(id, data) {
    return client.put(`/ai-managers/${id}`, data)
  },

  delete(id) {
    return client.delete(`/ai-managers/${id}`)
  },

  // ── Decision Triggers ────────────────────────────────────

  triggerDecision(managerId, source = 'manual') {
    return client.post(`/ai-managers/${managerId}/trigger`, { trigger_source: source })
  },

  triggerAll() {
    return client.post('/ai-managers/trigger-all')
  },

  // ── Decision Logs ────────────────────────────────────────

  decisionLogs(managerId, limit = 20) {
    return client.get(`/ai-managers/${managerId}/decisions`, { params: { limit } })
  },

  decisionLog(managerId, logId) {
    return client.get(`/ai-managers/${managerId}/decisions/${logId}`)
  },

  // ── Leaderboard & Charts ─────────────────────────────────

  leaderboard() {
    return client.get('/ai-managers/leaderboard')
  },

  comparisonChart() {
    return client.get('/ai-managers/comparison-chart')
  },
}
