<template>
  <v-app :theme="isDark ? 'dark' : 'light'">
    <v-navigation-drawer v-model="drawer" app clipped>
      <v-list-item
        prepend-avatar="/favicon.ico"
        title="FundBot AI"
        subtitle="AI Fund Management"
        class="pa-4"
      />
      <v-divider />
      <v-list nav density="compact">
        <v-list-item
          v-for="item in navItems"
          :key="item.title"
          :prepend-icon="item.icon"
          :title="item.title"
          :to="item.to"
          :value="item.title"
          color="primary"
        />
      </v-list>
    </v-navigation-drawer>

    <v-app-bar app clipped-left color="surface" elevation="0">
      <v-app-bar-nav-icon @click="drawer = !drawer" />
      <v-app-bar-title class="text-h6 font-weight-bold">
        FundBot AI
        <span class="text-caption text-medium-emphasis ml-2">AI-Powered Fund Management</span>
      </v-app-bar-title>
      <v-spacer />
      <v-btn icon @click="isDark = !isDark">
        <v-icon>{{ isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>
      <v-menu v-if="user" offset-y>
        <template v-slot:activator="{ props }">
          <v-btn icon v-bind="props">
            <v-icon>mdi-account-circle</v-icon>
          </v-btn>
        </template>
        <v-list density="compact">
          <v-list-item title="Profile" prepend-icon="mdi-account" />
          <v-list-item title="Settings" prepend-icon="mdi-cog" />
          <v-divider />
          <v-list-item title="Logout" prepend-icon="mdi-logout" @click="logout" />
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
import { ref, computed } from 'vue'
import { useTheme } from 'vuetify'
import { useAuthStore } from '@/stores/authStore'

const theme = useTheme()
const auth = useAuthStore()

const drawer = ref(true)
const isDark = ref(true)
const user = computed(() => auth.user)

const navItems = [
  { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/' },
  { title: 'Portfolios', icon: 'mdi-briefcase-variant', to: '/portfolios' },
  { title: 'Brokers', icon: 'mdi-link-variant', to: '/brokers' },
  { title: 'Performance', icon: 'mdi-chart-line', to: '/performance' },
  { title: 'Settings', icon: 'mdi-cog', to: '/settings' },
]

function logout() {
  auth.logout()
}
</script>

<style>
.v-app-bar {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
}
</style>
