/**
 * Pinia store for AI Manager Arena state.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import arenaApi from '@/services/arenaApi'

export const useArenaStore = defineStore('arena', () => {
  // ── State ──────────────────────────────────────────────

  const managers = ref([])
  const leaderboard = ref([])
  const comparisonSeries = ref([])
  const decisionLogs = ref([])
  const currentDecision = ref(null)
  const triggering = ref(false)
  const loading = ref(false)
  const error = ref(null)

  // ── Getters ────────────────────────────────────────────

  const activeManagers = computed(() =>
    managers.value.filter(m => m.is_active)
  )

  const topManager = computed(() =>
    leaderboard.value.length > 0 ? leaderboard.value[0] : null
  )

  // ── Actions ────────────────────────────────────────────

  async function fetchManagers() {
    loading.value = true
    error.value = null
    try {
      const res = await arenaApi.list()
      managers.value = res.data || []
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load AI managers'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createManager(data) {
    loading.value = true
    error.value = null
    try {
      const res = await arenaApi.create(data)
      managers.value.push(res.data)
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to create AI manager'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateManager(id, data) {
    loading.value = true
    error.value = null
    try {
      const res = await arenaApi.update(id, data)
      const idx = managers.value.findIndex(m => m.id === id)
      if (idx !== -1) managers.value[idx] = res.data
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to update AI manager'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteManager(id) {
    loading.value = true
    error.value = null
    try {
      await arenaApi.delete(id)
      managers.value = managers.value.filter(m => m.id !== id)
      leaderboard.value = leaderboard.value.filter(e => e.id !== id)
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to delete AI manager'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function triggerDecision(managerId) {
    triggering.value = true
    error.value = null
    try {
      const res = await arenaApi.triggerDecision(managerId)
      currentDecision.value = res.data
      await fetchLeaderboard()
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to trigger decision'
      throw e
    } finally {
      triggering.value = false
    }
  }

  async function triggerAll() {
    triggering.value = true
    error.value = null
    try {
      const res = await arenaApi.triggerAll()
      await fetchLeaderboard()
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to trigger all'
      throw e
    } finally {
      triggering.value = false
    }
  }

  async function fetchLeaderboard() {
    try {
      const res = await arenaApi.leaderboard()
      leaderboard.value = res.data?.entries || []
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load leaderboard'
      leaderboard.value = []
      throw e
    }
  }

  async function fetchComparisonChart() {
    try {
      const res = await arenaApi.comparisonChart()
      comparisonSeries.value = res.data?.series || []
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load comparison chart'
      comparisonSeries.value = []
      throw e
    }
  }

  async function fetchDecisionLogs(managerId, limit = 20) {
    try {
      const res = await arenaApi.decisionLogs(managerId, limit)
      decisionLogs.value = res.data || []
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load decision logs'
      decisionLogs.value = []
      throw e
    }
  }

  return {
    managers,
    leaderboard,
    comparisonSeries,
    decisionLogs,
    currentDecision,
    triggering,
    loading,
    error,
    activeManagers,
    topManager,
    fetchManagers,
    createManager,
    updateManager,
    deleteManager,
    triggerDecision,
    triggerAll,
    fetchLeaderboard,
    fetchComparisonChart,
    fetchDecisionLogs,
  }
})
