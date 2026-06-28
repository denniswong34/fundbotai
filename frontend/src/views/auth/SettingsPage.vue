<template>
  <div>
    <h2 class="text-h4 font-weight-bold mb-6">{{ $t('settings.title') }}</h2>

    <v-row>
      <v-col cols="12" md="6">
        <v-card class="glass-card" elevation="0">
          <v-card-title>{{ $t('settings.preferences') }}</v-card-title>
          <v-card-text>
            <v-select
              :model-value="settingsStore.language"
              :label="$t('settings.language')"
              :items="[
                { title: 'English', value: 'en' },
                { title: '繁體中文', value: 'zh_Hant' },
                { title: '简体中文', value: 'zh_Hans' },
              ]"
              item-title="title"
              item-value="value"
              variant="outlined"
              density="compact"
              class="mb-4"
              @update:model-value="onLanguageChange"
            />

            <v-select
              :model-value="settingsStore.theme"
              :label="$t('settings.theme')"
              :items="[
                { title: $t('settings.dark'), value: 'dark' },
                { title: $t('settings.light'), value: 'light' },
              ]"
              item-title="title"
              item-value="value"
              variant="outlined"
              density="compact"
              class="mb-4"
              @update:model-value="onThemeChange"
            />

            <v-text-field
              :model-value="settingsStore.timezone"
              :label="$t('settings.timezone')"
              variant="outlined"
              density="compact"
              class="mb-4"
              @update:model-value="onTimezoneChange"
            />

            <v-divider class="my-4" />

            <div class="text-subtitle-2 mb-3">{{ $t('settings.telegram') }}</div>
            <v-switch
              :model-value="settingsStore.telegramEnabled"
              :label="$t('settings.enable_telegram')"
              color="primary"
              density="compact"
              @update:model-value="onTelegramToggle"
            />
            <v-text-field
              v-if="settingsStore.telegramEnabled"
              :model-value="settingsStore.telegramChatId"
              :label="$t('settings.telegram_chat_id')"
              variant="outlined"
              density="compact"
              @update:model-value="onTelegramChatIdChange"
            />
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn color="primary" :loading="saving" @click="saveSettings">
              {{ $t('common.save') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useSettingsStore } from '@/stores/settingsStore'

const settingsStore = useSettingsStore()
const saving = ref(false)

function onLanguageChange(val) {
  settingsStore.setLanguage(val)
}

function onThemeChange(val) {
  settingsStore.setTheme(val)
}

function onTimezoneChange(val) {
  settingsStore.timezone = val
}

function onTelegramToggle(val) {
  settingsStore.telegramEnabled = val
}

function onTelegramChatIdChange(val) {
  settingsStore.telegramChatId = val
}

async function saveSettings() {
  saving.value = true
  try {
    await settingsStore.saveToBackend()
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}
</style>
