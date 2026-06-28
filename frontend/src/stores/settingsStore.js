/**
 * Pinia store for user settings (language, theme).
 *
 * Handles:
 * - Persistence to localStorage
 * - Sync to backend API
 * - Reactive theme and language state
 */

import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useTheme } from 'vuetify'
import axios from 'axios'
import i18n, { storeLanguage, detectLanguage } from '@/plugins/i18n'

export const useSettingsStore = defineStore('settings', () => {
  // ── State ────────────────────────────────────────────

  const language = ref('en')
  const theme = ref('dark')
  const timezone = ref('Asia/Hong_Kong')
  const telegramChatId = ref(null)
  const telegramEnabled = ref(false)
  const loaded = ref(false)
  const loading = ref(false)

  // ── Actions ──────────────────────────────────────────

  /**
   * Initialize settings from localStorage, then try to load from backend.
   */
  async function initialize() {
    // Load from localStorage first
    const saved = loadFromStorage()
    if (saved) {
      language.value = saved.language || 'en'
      theme.value = saved.theme || 'dark'
      timezone.value = saved.timezone || 'Asia/Hong_Kong'
      telegramEnabled.value = saved.telegramEnabled || false
    }

    // Apply initial theme
    applyTheme()

    // Try to load from backend (if authenticated)
    try {
      await loadFromBackend()
    } catch {
      // Not authenticated or API unavailable — use saved settings
    }

    loaded.value = true
  }

  /**
   * Set the language and persist it.
   */
  function setLanguage(lang) {
    if (!['en', 'zh_Hant', 'zh_Hans'].includes(lang)) return
    language.value = lang
    storeLanguage(lang)
    i18n.global.locale.value = lang
    saveToStorage()
    // Sync to backend in background
    saveToBackend().catch(() => {})
  }

  /**
   * Set the theme (dark/light) and persist it.
   */
  function setTheme(newTheme) {
    if (!['dark', 'light'].includes(newTheme)) return
    theme.value = newTheme
    applyTheme()
    saveToStorage()
    // Sync to backend in background
    saveToBackend().catch(() => {})
  }

  /**
   * Toggle between dark and light theme.
   */
  function toggleTheme() {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  /**
   * Apply the current theme to Vuetify.
   */
  function applyTheme() {
    try {
      const vuetifyTheme = useTheme()
      vuetifyTheme.global.name.value = theme.value
    } catch {
      // Vuetify not yet initialized
    }
    // Also set a data attribute for fallback CSS
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  /**
   * Load settings from the backend API.
   */
  async function loadFromBackend() {
    const token = localStorage.getItem('access_token')
    if (!token) return

    loading.value = true
    try {
      const response = await axios.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      const settings = response.data.settings
      if (settings) {
        language.value = settings.language || 'en'
        theme.value = settings.theme || 'dark'
        timezone.value = settings.timezone || 'Asia/Hong_Kong'
        telegramChatId.value = settings.telegram_chat_id || null
        telegramEnabled.value = settings.telegram_enabled || false

        // Apply loaded settings
        storeLanguage(language.value)
        i18n.global.locale.value = language.value
        applyTheme()
        saveToStorage()
      }
    } catch {
      // Backend unavailable — keep current settings
    } finally {
      loading.value = false
    }
  }

  /**
   * Save current settings to the backend API.
   */
  async function saveToBackend() {
    const token = localStorage.getItem('access_token')
    if (!token) return

    try {
      await axios.put(
        '/api/auth/settings',
        {
          language: language.value,
          theme: theme.value,
          timezone: timezone.value,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      )
    } catch {
      // Silently fail — settings are persisted in localStorage
    }
  }

  /**
   * Persist settings to localStorage.
   */
  function saveToStorage() {
    try {
      localStorage.setItem(
        'fundbotai_settings',
        JSON.stringify({
          language: language.value,
          theme: theme.value,
          timezone: timezone.value,
          telegramEnabled: telegramEnabled.value,
        }),
      )
    } catch {
      // localStorage may be unavailable
    }
  }

  /**
   * Load settings from localStorage.
   */
  function loadFromStorage() {
    try {
      const raw = localStorage.getItem('fundbotai_settings')
      if (raw) {
        return JSON.parse(raw)
      }
    } catch {
      // ignore parse errors
    }
    return null
  }

  // ── Return ───────────────────────────────────────────

  return {
    language,
    theme,
    timezone,
    telegramChatId,
    telegramEnabled,
    loaded,
    loading,
    initialize,
    setLanguage,
    setTheme,
    toggleTheme,
    applyTheme,
    loadFromBackend,
    saveToBackend,
  }
})
