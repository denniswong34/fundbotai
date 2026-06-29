<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="500">
    <v-card class="glass-card">
      <v-card-title>{{ $t('portfolio.add_holding') }}</v-card-title>
      <v-card-text>
        <v-form ref="form" @submit.prevent="submit">
          <v-text-field
            v-model="form.symbol"
            label="Symbol"
            :rules="[v => !!v || 'Symbol is required']"
            variant="outlined"
            density="compact"
            class="mb-3"
          />
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="form.target_weight_pct"
                :label="$t('portfolio.target_weight')"
                type="number"
                suffix="%"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="6">
              <v-select
                v-model="form.market"
                label="Market"
                :items="['US', 'HK', 'CN', 'JP', 'EU']"
                variant="outlined"
                density="compact"
                @update:model-value="onMarketChange"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="form.lot_size"
                label="Lot Size"
                type="number"
                variant="outlined"
                density="compact"
                :hint="marketHint"
                persistent-hint
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.current_shares"
                :label="$t('common.shares')"
                type="number"
                variant="outlined"
                density="compact"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="form.current_price"
                :label="$t('common.price')"
                type="number"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="6">
              <v-select
                v-model="form.asset_type"
                label="Asset Type"
                :items="['stock', 'etf', 'crypto']"
                variant="outlined"
                density="compact"
              />
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="$emit('update:modelValue', false)">{{ $t('common.cancel') }}</v-btn>
        <v-btn color="primary" :loading="saving" @click="submit">{{ $t('common.add') }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { usePortfolioStore } from '@/stores/portfolioStore'

const props = defineProps({
  modelValue: Boolean,
  portfolioId: { type: Number, required: true },
})

const emit = defineEmits(['update:modelValue', 'added'])

const portfolioStore = usePortfolioStore()
const saving = ref(false)
const form = reactive({
  symbol: '',
  target_weight_pct: 0,
  market: 'US',
  current_shares: 0,
  current_price: 0,
  lot_size: 1,
  asset_type: 'stock',
})

const marketHint = computed(() => {
  const hints = {
    'US': 'Min 1 share',
    'HK': 'Min 1 lot (100 shares)',
    'CN': 'Min 100 shares (1 lot)',
    'JP': 'Min 100 shares (1 lot)',
    'EU': 'Min 1 share',
  }
  return hints[form.market] || 'Min 1 share'
})

function onMarketChange(market) {
  const lots = { 'US': 1, 'HK': 100, 'CN': 100, 'JP': 100, 'EU': 1 }
  form.lot_size = lots[market] || 1
}

async function submit() {
  saving.value = true
  try {
    await portfolioStore.addHolding(props.portfolioId, { ...form })
    emit('added')
    emit('update:modelValue', false)
    form.symbol = ''
    form.target_weight_pct = 0
    form.market = 'US'
    form.lot_size = 1
    form.current_shares = 0
    form.current_price = 0
    form.asset_type = 'stock'
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
