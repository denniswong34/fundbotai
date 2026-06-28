<template>
  <v-app :theme="themeClass">
    <v-navigation-drawer v-model="drawer" app clipped>
      <v-list-item
        prepend-avatar="/favicon.ico"
        :title="$t('common.app_name')"
        subtitle="AI Fund Management"
        class="pa-4"
      />
      <v-divider />
      <v-list nav density="compact">
        <v-list-item
          v-for="item in navItems"
          :key="item.title"
          :prepend-icon="item.icon"
          :title="$t(item.titleKey)"
          :to="item.to"
          :value="item.title"
          color="primary"
        />
      </v-list>
      <template v-slot:append>
        <v-divider class="mb-2" />
        <v-list nav density="compact">
          <v-list-item
            prepend-icon="mdi-cog"
            :title="$t('nav.settings')"
            to="/settings"
            color="primary"
          />
        </v-list>
      </template>
    </v-navigation-drawer>

    <v-app-bar app clipped-left color="surface" elevation="0">
      <v-app-bar-nav-icon @click="drawer = !drawer" />
      <v-app-bar-title class="text-h6 font-weight-bold">
        {{ $t('common.app_name') }}
        <span class="text-caption text-medium-emphasis ml-2">AI-Powered Fund Management</span>
      </v-app-bar-title>
      <v-spacer />
      <LanguageSwitcher />
      <ThemeToggle />
      <v-menu v-if="user" offset-y>
        <template v-slot:activator="{ props }">
          <v-btn icon v-bind="props" variant="text">
            <v-icon>mdi-account-circle</v-icon>
          </v-btn>
        </template>
        <v-list density="compact">
          <v-list-item :title="$t('nav.settings')" prepend-icon="mdi-cog" to="/settings" />
          <v-divider />
          <v-list-item :title="$t('common.logout')" prepend-icon="mdi-logout" @click="logout" />
        </v-list>
      </v-menu>
    </v-app-bar>

    <v-main class="bg-background">
      <v-container fluid class="pa-6">
        <router-view />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useSettingsStore } from '@/stores/settingsStore'
import LanguageSwitcher from '@/components/common/LanguageSwitcher.vue'
import ThemeToggle from '@/components/common/ThemeToggle.vue'

const auth = useAuthStore()
const settingsStore = useSettingsStore()

const drawer = ref(true)
const user = computed(() => auth.user)
const themeClass = computed(() => settingsStore.theme)

const navItems = [
  { title: 'Dashboard', titleKey: 'nav.dashboard', icon: 'mdi-view-dashboard', to: '/' },
  { title: 'Portfolios', titleKey: 'nav.portfolios', icon: 'mdi-briefcase-variant', to: '/portfolios' },
  { title: 'Brokers', titleKey: 'nav.brokers', icon: 'mdi-link-variant', to: '/brokers' },
  { title: 'Performance', titleKey: 'nav.performance', icon: 'mdi-chart-line', to: '/performance' },
]

onMounted(() => {
  settingsStore.initialize()
})

function logout() {
  auth.logout()
}
</script>

<style>
.v-app-bar {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
}
</style>
