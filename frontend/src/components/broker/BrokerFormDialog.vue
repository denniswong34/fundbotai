<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="600" persistent>
    <v-card class="glass-card">
      <v-card-title>{{ isEdit ? $t('common.edit_broker') : $t('common.add_broker') }}</v-card-title>
      <v-card-text>
        <v-form ref="formRef" @submit.prevent="submit">

          <!-- Broker Name -->
          <v-text-field
            v-model="form.name"
            :label="$t('common.name')"
            :rules="[v => !!v?.trim() || 'Name is required']"
            variant="outlined"
            density="compact"
            class="mb-3"
          />

          <!-- Broker Type -->
          <v-select
            v-model="form.broker_type"
            :label="$t('common.type')"
            :items="brokerTypes"
            item-title="name"
            item-value="type"
            :rules="[v => !!v || 'Type is required']"
            variant="outlined"
            density="compact"
            class="mb-3"
            @update:model-value="onTypeChange"
            return-object
            :disabled="isEdit"
          />

          <!-- Market Type -->
          <v-select
            v-model="form.market_type"
            :label="$t('common.market')"
            :items="marketOptions"
            item-title="label"
            item-value="value"
            variant="outlined"
            density="compact"
            class="mb-3"
          />

          <!-- Sandbox / Live Toggle -->
          <div class="sandbox-row mb-3">
            <v-switch
              v-model="form.sandbox"
              :label="form.sandbox ? '🧪 Sandbox / Testnet' : '🚀 Live / Production'"
              :color="form.sandbox ? 'warning' : 'success'"
              hide-details
              density="compact"
            />
            <div class="sandbox-hint text-caption text-medium-emphasis">
              {{ form.sandbox
                ? 'Safe testing environment — no real money'
                : 'Real trading — real money will be used' }}
            </div>
          </div>

          <!-- Dynamic config fields based on broker type -->
          <div v-if="dynamicFields.length" class="config-section">
            <div class="config-section-title text-subtitle-2 font-weight-bold mb-2">
              {{ $t('common.api_config') }}
            </div>
            <template v-for="field in dynamicFields" :key="field.key">
              <!-- Boolean fields (toggle) -->
              <v-switch
                v-if="field.type === 'boolean'"
                v-model="form.config_json[field.key]"
                :label="field.title"
                :color="'primary'"
                hide-details
                density="compact"
                class="mb-2"
              />
              <!-- Select/enum fields -->
              <v-select
                v-else-if="field.enum"
                v-model="form.config_json[field.key]"
                :label="field.title"
                :items="field.enum"
                variant="outlined"
                density="compact"
                class="mb-3"
              />
              <!-- Password fields -->
              <v-text-field
                v-else-if="field.format === 'password'"
                v-model="form.config_json[field.key]"
                :label="field.title"
                type="password"
                variant="outlined"
                density="compact"
                class="mb-3"
              />
              <!-- Number fields -->
              <v-text-field
                v-else-if="field.type === 'number' || field.type === 'integer'"
                v-model.number="form.config_json[field.key]"
                :label="field.title"
                type="number"
                variant="outlined"
                density="compact"
                class="mb-3"
              />
              <!-- Default text fields -->
              <v-text-field
                v-else
                v-model="form.config_json[field.key]"
                :label="field.title"
                variant="outlined"
                density="compact"
                class="mb-3"
              />
            </template>
          </div>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-btn
          variant="outlined"
          color="primary"
          :loading="testing"
          @click="testNow"
          class="mr-auto"
          :disabled="isEdit"
        >
          <v-icon left>mdi-flash</v-icon>
          {{ $t('common.test_connection') }}
        </v-btn>
        <v-spacer />
        <v-btn variant="text" @click="close">{{ $t('common.cancel') }}</v-btn>
        <v-btn color="primary" :loading="saving" @click="submit">{{ isEdit ? $t('common.save') : $t('common.save') }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import brokerApi from '@/services/brokerApi'

const props = defineProps({
  modelValue: Boolean,
  brokerId: { type: [Number, String], default: null },
})

const emit = defineEmits(['update:modelValue', 'saved'])

const formRef = ref(null)
const brokerTypes = ref([])
const selectedType = ref(null)
const saving = ref(false)
const testing = ref(false)
const loading = ref(false)

const isEdit = computed(() => !!props.brokerId)

const form = ref({
  name: '',
  broker_type: '',
  market_type: 'stocks',
  sandbox: true,
  config_json: {},
})

const marketOptions = [
  { label: 'Stocks', value: 'stocks' },
  { label: 'Crypto', value: 'crypto' },
  { label: 'Both', value: 'both' },
]

// Compute dynamic config fields from the selected broker type's schema
const dynamicFields = computed(() => {
  const schema = selectedType.value?.config_schema
  if (!schema?.properties) return []
  const props = schema.properties
  return Object.entries(props).map(([key, prop]) => ({
    key,
    title: prop.title || key,
    type: prop.type,
    format: prop.format,
    enum: prop.enum || null,
    default: prop.default,
  }))
})

function onTypeChange(item) {
  selectedType.value = item || null
  // Reset config for new type
  form.value.config_json = {}
  if (selectedType.value?.config_schema?.properties) {
    for (const [key, prop] of Object.entries(selectedType.value.config_schema.properties)) {
      form.value.config_json[key] = prop.default !== undefined ? prop.default : ''
    }
  }
}

async function loadTypes() {
  try {
    const res = await brokerApi.getTypes()
    brokerTypes.value = res.data
  } catch (e) {
    console.error('Failed to load broker types:', e)
    brokerTypes.value = []
  }
}

async function loadExisting() {
  if (!props.brokerId) return
  loading.value = true
  try {
    const res = await brokerApi.get(props.brokerId)
    const data = res.data
    form.value = {
      name: data.name || '',
      broker_type: data.broker_type || '',
      market_type: data.market_type || 'stocks',
      sandbox: data.sandbox !== false,
      config_json: data.config_json || {},
    }
    // Set the selected type schema to match the broker's type
    const match = brokerTypes.value.find(t => t.type === data.broker_type)
    if (match) {
      selectedType.value = match
    }
  } catch (e) {
    console.error('Failed to load broker:', e)
  } finally {
    loading.value = false
  }
}

async function testNow() {
  testing.value = true
  try {
    const res = await brokerApi.create({ ...form.value })
    const testRes = await brokerApi.test(res.data.id)
    await brokerApi.delete(res.data.id)
    console.log('Test result:', testRes.data.success ? 'OK' : 'FAILED')
  } catch (e) {
    console.error('Test failed:', e)
  } finally {
    testing.value = false
  }
}

async function submit() {
  const { valid } = await formRef.value?.validate() || { valid: false }
  if (!valid) return

  saving.value = true
  try {
    if (isEdit.value) {
      await brokerApi.update(props.brokerId, { ...form.value })
    } else {
      await brokerApi.create({ ...form.value })
    }
    emit('saved')
    close()
  } catch (e) {
    console.error('Save failed:', e)
  } finally {
    saving.value = false
  }
}

function close() {
  form.value = {
    name: '',
    broker_type: '',
    market_type: 'stocks',
    sandbox: true,
    config_json: {},
  }
  selectedType.value = null
  formRef.value?.reset()
  emit('update:modelValue', false)
}

// Reload types and data whenever dialog opens
watch(() => props.modelValue, async (open) => {
  if (open) {
    await loadTypes()
    if (isEdit.value) {
      await loadExisting()
    }
  }
})
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}
.sandbox-row {
  padding: 8px 0;
}
.sandbox-hint {
  margin-top: -8px;
  padding-left: 8px;
}
.config-section {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
</style>
