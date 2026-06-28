<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="700">
    <v-card class="glass-card">
      <v-card-title>
        {{ portfolio ? $t('portfolio.edit') : $t('portfolio.create') }}
      </v-card-title>
      <v-card-text>
        <v-form ref="form" @submit.prevent="submit">
          <v-text-field
            v-model="formData.name"
            :label="$t('common.name')"
            :rules="[v => !!v || 'Name is required']"
            variant="outlined"
            density="compact"
            class="mb-3"
          />
          <v-textarea
            v-model="formData.description"
            :label="$t('common.description')"
            variant="outlined"
            density="compact"
            rows="2"
            class="mb-3"
          />
          <v-row>
            <v-col cols="6">
              <v-select
                v-model="formData.base_currency"
                :label="$t('common.currency')"
                :items="['USD', 'EUR', 'GBP', 'HKD', 'CNY', 'JPY']"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="6">
              <v-select
                v-model="formData.broker_connection_id"
                :label="$t('common.broker')"
                :items="brokerOptions"
                item-title="name"
                item-value="id"
                variant="outlined"
                density="compact"
                clearable
              />
            </v-col>
          </v-row>

          <v-divider class="my-3" />

          <div class="text-subtitle-2 mb-2">{{ $t('portfolio.rebalance_config') }}</div>
          <v-row>
            <v-col cols="6">
              <v-select
                v-model="formData.rebalance_order_type"
                :label="$t('portfolio.order_type')"
                :items="['market', 'limit']"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="formData.drift_threshold_pct"
                :label="$t('portfolio.drift_threshold')"
                type="number"
                suffix="%"
                variant="outlined"
                density="compact"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="formData.cash_reserve_pct"
                :label="$t('portfolio.cash_reserve')"
                type="number"
                suffix="%"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="6">
              <v-select
                v-model="formData.rebalance_frequency"
                :label="$t('portfolio.rebalance_frequency')"
                :items="['drift_only', 'daily', 'weekly', 'monthly', 'quarterly']"
                variant="outlined"
                density="compact"
              />
            </v-col>
          </v-row>
          <v-switch
            v-model="formData.auto_rebalance_enabled"
            :label="$t('portfolio.auto_rebalance')"
            color="primary"
            density="compact"
            class="mt-2"
          />

          <!-- Initial Holdings Input -->
          <v-divider class="my-3" />
          <div class="text-subtitle-2 mb-2">{{ $t('portfolio.initial_holdings') }}</div>
          <div v-for="(h, i) in formData.holdings" :key="i" class="d-flex ga-2 mb-2 align-center">
            <v-text-field v-model="h.symbol" label="Symbol" density="compact" variant="outlined" hide-details style="max-width: 100px" />
            <v-text-field v-model="h.target_weight_pct" label="Weight %" type="number" density="compact" variant="outlined" hide-details style="max-width: 100px" />
            <v-text-field v-model="h.market" label="Market" density="compact" variant="outlined" hide-details style="max-width: 80px" />
            <v-btn icon size="small" color="error" variant="text" @click="removeHolding(i)">
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </div>
          <v-btn size="small" variant="text" prepend-icon="mdi-plus" @click="addHoldingRow" class="mt-1">
            {{ $t('portfolio.add_holding') }}
          </v-btn>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="$emit('update:modelValue', false)">{{ $t('common.cancel') }}</v-btn>
        <v-btn color="primary" :loading="saving" @click="submit">{{ $t('common.save') }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { usePortfolioStore } from '@/stores/portfolioStore'
import brokerApi from '@/services/brokerApi'

const props = defineProps({
  modelValue: Boolean,
  portfolio: { type: Object, default: null },
})

const emit = defineEmits(['update:modelValue', 'created', 'updated'])

const portfolioStore = usePortfolioStore()
const form = ref(null)
const saving = ref(false)
const brokerOptions = ref([])

const formData = ref({
  name: '',
  description: '',
  base_currency: 'USD',
  broker_connection_id: null,
  rebalance_order_type: 'market',
  drift_threshold_pct: 5.00,
  cash_reserve_pct: 0.00,
  auto_rebalance_enabled: false,
  rebalance_frequency: 'drift_only',
  holdings: [],
})

function addHoldingRow() {
  formData.value.holdings.push({ symbol: '', target_weight_pct: 0, market: 'US' })
}

function removeHolding(idx) {
  formData.value.holdings.splice(idx, 1)
}

async function submit() {
  saving.value = true
  try {
    if (props.portfolio) {
      await portfolioStore.updatePortfolio(props.portfolio.id, formData.value)
      emit('updated')
    } else {
      await portfolioStore.createPortfolio(formData.value)
      emit('created')
    }
    emit('update:modelValue', false)
  } finally {
    saving.value = false
  }
}

async function loadBrokers() {
  try {
    const res = await brokerApi.list()
    brokerOptions.value = res.data
  } catch {
    brokerOptions.value = []
  }
}

watch(() => props.modelValue, (val) => {
  if (val) {
    loadBrokers()
    if (props.portfolio) {
      formData.value = {
        name: props.portfolio.name || '',
        description: props.portfolio.description || '',
        base_currency: props.portfolio.base_currency || 'USD',
        broker_connection_id: props.portfolio.broker_connection_id || null,
        rebalance_order_type: props.portfolio.rebalance_order_type || 'market',
        drift_threshold_pct: Number(props.portfolio.drift_threshold_pct || 5.00),
        cash_reserve_pct: Number(props.portfolio.cash_reserve_pct || 0.00),
        auto_rebalance_enabled: props.portfolio.auto_rebalance_enabled || false,
        rebalance_frequency: props.portfolio.rebalance_frequency || 'drift_only',
        holdings: [],
      }
    } else {
      formData.value = {
        name: '',
        description: '',
        base_currency: 'USD',
        broker_connection_id: null,
        rebalance_order_type: 'market',
        drift_threshold_pct: 5.00,
        cash_reserve_pct: 0.00,
        auto_rebalance_enabled: false,
        rebalance_frequency: 'drift_only',
        holdings: [],
      }
    }
  }
})

onMounted(() => {
  loadBrokers()
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
