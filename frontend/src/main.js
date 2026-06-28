/**
 * FundBot AI Frontend — Application Entry Point
 *
 * Initializes Vue 3 with:
 * - Pinia state management
 * - Vue Router
 * - Vuetify 3 UI framework
 * - Vue I18n internationalization
 * - Settings store for theme/language persistence
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi-svg'

// Styles
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'

// App & Router
import App from './App.vue'
import router from './router'

// Plugins
import i18n from '@/plugins/i18n'

// Create Vuetify instance
const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        dark: true,
        colors: {
          background: '#121212',
          surface: '#1E1E1E',
          primary: '#4CAF50',
          secondary: '#03DAC6',
          accent: '#FF4081',
          error: '#CF6679',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FB8C00',
        },
      },
      light: {
        dark: false,
        colors: {
          background: '#F5F5F5',
          surface: '#FFFFFF',
          primary: '#2E7D32',
          secondary: '#00897B',
          accent: '#D81B60',
          error: '#B00020',
          info: '#1976D2',
          success: '#388E3C',
          warning: '#F57C00',
        },
      },
    },
  },
  defaults: {
    VCard: {
      elevation: 1,
    },
    VBtn: {
      variant: 'flat',
    },
  },
})

// Create Vue app
const app = createApp(App)

// Register plugins
app.use(createPinia())
app.use(router)
app.use(vuetify)
app.use(i18n)

// Mount
app.mount('#app')
