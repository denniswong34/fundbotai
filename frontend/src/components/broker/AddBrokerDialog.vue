<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="600">
    <v-card class="glass-card">
      <v-card-title>{{ $t('common.add_broker') }}</v-card-title>
      <v-card-text>
        <v-form ref="form" @submit.prevent="submit">
          <v-text-field
            v-model="form.name"
            :label="$t('common.name')"
            :rules="[v => !!v || 'Name is required']"
            variant="outlined"
            density="compact"
            class="mb-3"
          />
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
          />
          <v-select
            v-model="form.market_type"
            :label="$t('common.market')"
            :items="['stocks', 'crypto', 'both']"
            variant="outlined"
            density="compact"
            class="mb-3"
          />

          <!-- Dynamic config fields based on broker type -->
          <div v-if="selectedType?.config_schema?.properties">
            <v-text-field
              v-for="(prop, key) in selectedType.config_schema.properties"
              :key="key"
              v-model="form.config_json[key]"
              :label="prop.title || key"
              :type="prop.format === 'password' ? 'password' : 'text'"
              variant="outlined"
              density="compact"
              class="mb-3"
            />
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
        >
          <v-icon left>mdi-flash</v-icon>
          {{ $t('common.test_connection') }}
        </v-btn>
        <v-btn variant="text" @click="$emit('update:modelValue', false)">{{ $t('common.cancel') }}</v-btn>
        <v-btn color="primary" :loading="saving" @click="submit">{{ $t('common.save') }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import brokerApi from '@/services/brokerApi'

const props = defineProps({
  modelValue: Boolean,
})

const emit = defineEmits(['update:modelValue', 'created'])

const brokerTypes = ref([])
const selectedType = ref(null)
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)

const form = reactive({
  name: '',
  broker_type: '',
  market_type: 'stocks',
  config_json: {},
})

async function loadTypes() {
  try {
    const res = await brokerApi.getTypes()
    brokerTypes.value = res.data
  } catch {
    brokerTypes.value = []
  }
}

function onTypeChange(typeKey) {
  selectedType.value = brokerTypes.value.find((t) => t.type === typeKey)
  // Reset config
  form.config_json = {}
  if (selectedType.value?.config_schema?.properties) {
    for (const [key, prop] of Object.entries(selectedType.value.config_schema.properties)) {
      form.config_json[key] = prop.default || ''
    }
  }
}

async function testNow() {
  testing.value = true
  testResult.value = null
  try {
    // First save temporarily, then test
    const res = await brokerApi.create({ ...form })
    const testRes = await brokerApi.test(res.data.id)
    await brokerApi.delete(res.data.id)
    testResult.value = testRes.data.success
  } catch {
    testResult.value = false
  } finally {
    testing.value = false
  }
}

async function submit() {
  saving.value = true
  try {
    await brokerApi.create({ ...form })
    emit('created')
    emit('update:modelValue', false)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadTypes()
})
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}
</style>
