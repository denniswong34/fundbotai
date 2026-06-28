<template>
  <v-menu offset-y>
    <template v-slot:activator="{ props }">
      <v-btn icon v-bind="props" variant="text" size="small">
        <v-icon>mdi-translate</v-icon>
      </v-btn>
      <v-tooltip activator="parent" location="bottom">
        {{ $t('settings.language') }}
      </v-tooltip>
    </template>

    <v-list density="compact" lines="one" class="pa-1">
      <v-list-item
        v-for="lang in languages"
        :key="lang.code"
        :value="lang.code"
        :active="currentLang === lang.code"
        color="primary"
        density="compact"
        class="rounded"
        @click="switchLanguage(lang.code)"
      >
        <template v-slot:prepend>
          <v-icon
            :color="currentLang === lang.code ? 'primary' : undefined"
            size="small"
            class="mr-2"
          >
            {{ currentLang === lang.code ? 'mdi-check-circle' : 'mdi-circle-outline' }}
          </v-icon>
        </template>
        <v-list-item-title
          :class="{ 'font-weight-bold': currentLang === lang.code }"
        >
          {{ lang.label }}
        </v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSettingsStore } from '@/stores/settingsStore'

const { locale } = useI18n()
const settingsStore = useSettingsStore()

const currentLang = computed(() => locale.value)

const languages = [
  { code: 'en', label: 'English' },
  { code: 'zh_Hant', label: '繁體中文' },
  { code: 'zh_Hans', label: '简体中文' },
]

function switchLanguage(code) {
  settingsStore.setLanguage(code)
}
</script>
