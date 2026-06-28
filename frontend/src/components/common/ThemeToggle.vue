<template>
  <v-btn
    icon
    variant="text"
    size="small"
    @click="settingsStore.toggleTheme()"
  >
    <v-icon>{{ isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
    <v-tooltip activator="parent" location="bottom">
      {{ isDark ? $t('settings.light') : $t('settings.dark') }}
    </v-tooltip>
  </v-btn>
</template>

<script setup>
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settingsStore'

const settingsStore = useSettingsStore()

const isDark = computed(() => settingsStore.theme === 'dark')
</script>
