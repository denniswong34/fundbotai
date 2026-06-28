/**
 * Vue I18n plugin setup for FundBot AI.
 *
 * Language detection priority:
 *   1. URL query parameter (?lang=...)
 *   2. localStorage (persisted user preference)
 *   3. Backend UserSettings (loaded via API)
 *   4. Browser navigator.language
 *   5. Default: 'en'
 */

import { createI18n } from 'vue-i18n'

// Import locale messages
import en from '@/locales/en.json'
import zhHant from '@/locales/zh_Hant.json'
import zhHans from '@/locales/zh_Hans.json'

/**
 * Detect the user's preferred language based on priority chain.
 */
export function detectLanguage(savedLanguage = null) {
  // 1. URL param has highest priority
  const urlParams = new URLSearchParams(window.location.search)
  const urlLang = urlParams.get('lang')
  if (urlLang && ['en', 'zh_Hant', 'zh_Hans'].includes(urlLang)) {
    return urlLang
  }

  // 2. localStorage (already saved preference)
  if (savedLanguage && ['en', 'zh_Hant', 'zh_Hans'].includes(savedLanguage)) {
    return savedLanguage
  }

  // 3. Browser language
  const browserLang = navigator.language || navigator.userLanguage
  if (browserLang) {
    if (browserLang.startsWith('zh')) {
      // Map browser lang to our supported variants
      if (browserLang === 'zh-TW' || browserLang === 'zh-HK') {
        return 'zh_Hant'
      }
      if (browserLang === 'zh-CN' || browserLang === 'zh-SG') {
        return 'zh_Hans'
      }
      // Default to Simplified Chinese for generic 'zh'
      return 'zh_Hans'
    }
  }

  // 4. Default
  return 'en'
}

/**
 * Get the stored language from localStorage.
 */
export function getStoredLanguage() {
  try {
    return localStorage.getItem('fundbotai_language')
  } catch {
    return null
  }
}

/**
 * Store the language preference in localStorage.
 */
export function storeLanguage(lang) {
  try {
    localStorage.setItem('fundbotai_language', lang)
  } catch {
    // localStorage may be unavailable
  }
}

// Detect initial language
const storedLang = getStoredLanguage()
const initialLocale = detectLanguage(storedLang)

// Create i18n instance
const i18n = createI18n({
  legacy: false,        // Use Composition API mode
  locale: initialLocale,
  fallbackLocale: 'en',
  globalInjection: true,
  messages: {
    en,
    zh_Hant: zhHant,
    zh_Hans: zhHans,
  },
  silentTranslationWarn: true,
  missingWarn: false,
})

export default i18n
