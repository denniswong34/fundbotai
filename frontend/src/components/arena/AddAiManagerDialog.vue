<template>
  <v-dialog v-model="show" max-width="520" persistent>
    <v-card class="glass-dialog">
      <v-card-title>
        <v-icon start>mdi-robot</v-icon>
        {{ $t('arena.add_manager') }}
      </v-card-title>
      <v-card-text>
        <v-text-field
          v-model="form.name"
          :label="$t('common.name')"
          variant="outlined"
          density="compact"
          class="mb-3"
          hide-details
          required
        />

        <v-text-field
          v-model="form.model_name"
          label="Model Name"
          variant="outlined"
          density="compact"
          class="mb-3"
          hide-details
          placeholder="e.g. deepseek-v4-flash"
          required
        />

        <v-row class="mb-3">
          <v-col cols="6">
            <v-text-field
              v-model.number="form.temperature"
              label="Temperature"
              type="number"
              step="0.1"
              min="0"
              max="2"
              variant="outlined"
              density="compact"
              hide-details
            />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model.number="form.max_tokens"
              label="Max Tokens"
              type="number"
              step="500"
              min="500"
              max="16000"
              variant="outlined"
              density="compact"
              hide-details
            />
          </v-col>
        </v-row>

        <v-select
          v-model="form.run_frequency"
          :items="frequencyOptions"
          item-title="text"
          item-value="value"
          :label="$t('arena.run_frequency')"
          variant="outlined"
          density="compact"
          class="mb-3"
          hide-details
        />

        <v-textarea
          v-model="form.description"
          :label="$t('common.description')"
          variant="outlined"
          density="compact"
          rows="2"
          class="mb-3"
          hide-details
        />

        <v-switch
          v-model="form.auto_run_enabled"
          :label="$t('arena.auto_run')"
          color="primary"
          density="compact"
          hide-details
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">{{ $t('common.cancel') }}</v-btn>
        <v-btn color="primary" variant="flat" @click="submit" :loading="submitting">
          {{ $t('common.save') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useArenaStore } from '@/stores/arenaStore'

const props = defineProps({
  modelValue: Boolean,
})
const emit = defineEmits(['update:modelValue', 'created'])

const store = useArenaStore()
const submitting = ref(false)

const show = ref(false)
watch(() => props.modelValue, (v) => { show.value = v })
watch(show, (v) => { emit('update:modelValue', v) })

const frequencyOptions = [
  { text: 'Manual Only', value: 'manual' },
  { text: 'Daily', value: 'daily' },
  { text: 'Weekly', value: 'weekly' },
]

const form = ref({
  name: '',
  description: '',
  model_name: 'deepseek-v4-flash',
  model_provider: 'opencode-go',
  temperature: 0.7,
  max_tokens: 4000,
  run_frequency: 'daily',
  auto_run_enabled: false,
})

function resetForm() {
  form.value = {
    name: '',
    description: '',
    model_name: 'deepseek-v4-flash',
    model_provider: 'opencode-go',
    temperature: 0.7,
    max_tokens: 4000,
    run_frequency: 'daily',
    auto_run_enabled: false,
  }
}

async function submit() {
  if (!form.value.name || !form.value.model_name) return
  submitting.value = true
  try {
    await store.createManager({ ...form.value })
    show.value = false
    resetForm()
    emit('created')
  } catch (e) {
    // Store handles error
  } finally {
    submitting.value = false
  }
}

function close() {
  show.value = false
  resetForm()
}
</script>

<style scoped>
.glass-dialog {
  background: rgba(30, 30, 40, 0.98) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.08);
}
</style>
