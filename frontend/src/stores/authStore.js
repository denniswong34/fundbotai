/**
 * Pinia store for authentication state.
 *
 * Manages login, logout, token storage, and user profile.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // ── State ────────────────────────────────────────────

  const user = ref(null)
  const organization = ref(null)
  const settings = ref(null)
  const token = ref(localStorage.getItem('access_token') || null)
  const refreshTokenValue = ref(localStorage.getItem('refresh_token') || null)
  const loading = ref(false)
  const initialized = ref(false)

  // ── Getters ──────────────────────────────────────────

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // ── Actions ──────────────────────────────────────────

  /**
   * Initialize auth state from stored tokens.
   */
  async function initialize() {
    if (!token.value) {
      initialized.value = true
      return
    }

    try {
      await fetchProfile()
    } catch {
      // Token expired or invalid — clear state
      clearAuth()
    }
    initialized.value = true
  }

  /**
   * Login with username and password.
   */
  async function login(username, password) {
    loading.value = true
    try {
      const response = await axios.post('/api/auth/login', { username, password })
      const data = response.data

      // Store tokens
      token.value = data.access_token
      refreshTokenValue.value = data.refresh_token
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)

      // Set default auth header
      axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`

      // Store user, org, settings
      user.value = data.user
      organization.value = data.organization
      settings.value = data.settings

      return data
    } finally {
      loading.value = false
    }
  }

  /**
   * Register a new user.
   */
  async function register(username, email, password, displayName = null) {
    loading.value = true
    try {
      const response = await axios.post('/api/auth/register', {
        username,
        email,
        password,
        display_name: displayName,
      })
      const data = response.data

      // Store tokens
      token.value = data.access_token
      refreshTokenValue.value = data.refresh_token
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)

      axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`

      user.value = data.user
      organization.value = data.organization
      settings.value = data.settings

      return data
    } finally {
      loading.value = false
    }
  }

  /**
   * Logout the current user.
   */
  function logout() {
    clearAuth()
    router.push('/login')
  }

  /**
   * Fetch the current user profile from the API.
   */
  async function fetchProfile() {
    if (!token.value) return

    try {
      const response = await axios.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${token.value}` },
      })
      user.value = response.data.user
      organization.value = response.data.organization
      settings.value = response.data.settings
    } catch (error) {
      if (error.response?.status === 401) {
        // Try refreshing the token
        const refreshed = await refreshToken()
        if (refreshed) {
          const response = await axios.get('/api/auth/me', {
            headers: { Authorization: `Bearer ${token.value}` },
          })
          user.value = response.data.user
          organization.value = response.data.organization
          settings.value = response.data.settings
        } else {
          throw error
        }
      } else {
        throw error
      }
    }
  }

  /**
   * Refresh the access token using the refresh token.
   */
  async function refreshToken() {
    if (!refreshTokenValue.value) return false

    try {
      const response = await axios.post('/api/auth/refresh', {
        refresh_token: refreshTokenValue.value,
      })
      token.value = response.data.access_token
      refreshTokenValue.value = response.data.refresh_token
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`
      return true
    } catch {
      clearAuth()
      return false
    }
  }

  /**
   * Update local settings after backend sync.
   */
  function updateSettings(newSettings) {
    settings.value = newSettings
  }

  /**
   * Clear all auth state.
   */
  function clearAuth() {
    user.value = null
    organization.value = null
    settings.value = null
    token.value = null
    refreshTokenValue.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    delete axios.defaults.headers.common['Authorization']
  }

  return {
    user,
    organization,
    settings,
    token,
    refreshTokenValue,
    loading,
    initialized,
    isAuthenticated,
    isAdmin,
    initialize,
    login,
    register,
    logout,
    fetchProfile,
    refreshToken,
    updateSettings,
    clearAuth,
  }
})
