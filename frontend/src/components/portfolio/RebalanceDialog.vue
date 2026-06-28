<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="800">
    <v-card class="glass-card">
      <v-card-title>
        {{ $t('portfolio.rebalance_preview') }}
        <v-spacer />
        <v-chip size="small" variant="flat" color="primary">
          {{ $t('portfolio.total_value') }}: {{ formatCurrency(plan?.total_value || 0) }}
        </v-chip>
      </v-card-title>
      <v-card-text v-if="loading" class="text-center py-6">
        <v-progress-circular indeterminate color="primary" />
      </v-card-text>
      <v-card-text v-else-if="plan">
        <v-table density="compact">
          <thead>
            <tr>
              <th class="text-left">{{ $t('common.symbol') }}</th>
              <th class="text-right">{{ $t('portfolio.current_weight') }}</th>
              <th class="text-right">{{ $t('portfolio.target_weight') }}</th>
              <th class="text-right">{{ $t('portfolio.target_value') }}</th>
              <th class="text-right">{{ $t('portfolio.diff') }}</th>
              <th class="text-right">{{ $t('common.shares') }}</th>
              <th class="text-center">{{ $t('common.side') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in plan.orders" :key="o.symbol">
              <td><strong>{{ o.symbol }}</strong></td>
              <td class="text-right">{{ Number(o.current_weight_pct).toFixed(2) }}%</td>
              <td class="text-right">{{ Number(o.target_weight_pct).toFixed(2) }}%</td>
              <td class="text-right mono">{{ formatCurrency(o.target_value) }}</td>
              <td class="text-right mono">{{ formatCurrency(o.diff_value) }}</td>
              <td class="text-right mono">{{ Number(o.diff_shares).toFixed(2) }}</td>
              <td class="text-center">
                <v-chip
                  :color="o.side === 'buy' ? 'success' : 'error'"
                  size="x-small"
                  variant="flat"
                >
                  {{ o.side.toUpperCase() }}
                </v-chip>
              </td>
            </tr>
          </tbody>
        </v-table>

        <v-row class="mt-4">
          <v-col cols="6">
            <v-select
              v-model="orderType"
              :label="$t('portfolio.order_type')"
              :items="['market', 'limit']"
              variant="outlined"
              density="compact"
            />
          </v-col>
          <v-col cols="6" class="d-flex align-center">
            <div class="text-body-2">
              <strong>{{ $t('portfolio.estimated_cost') }}:</strong>
              {{ formatCurrency(plan.total_cost_estimate) }}
            </div>
          </v-col>
        </v-row>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="$emit('update:modelValue', false)">{{ $t('common.cancel') }}</v-btn>
        <v-btn color="warning" :loading="executing" @click="execute">
          {{ $t('portfolio.execute_rebalance') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { usePortfolioStore } from '@/stores/portfolioStore'

const props = defineProps({
  modelValue: Boolean,
  portfolioId: { type: Number, required: true },
})

const emit = defineEmits(['update:modelValue', 'executed'])

const portfolioStore = usePortfolioStore()
const plan = ref(null)
const loading = ref(false)
const executing = ref(false)
const orderType = ref('market')

function formatCurrency(val) {
  const num = Number(val || 0)
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(num)
}

async function loadPlan() {
  loading.value = true
  try {
    plan.value = await portfolioStore.rebalancePlan(props.portfolioId)
  } finally {
    loading.value = false
  }
}

async function execute() {
  executing.value = true
  try {
    await portfolioStore.rebalanceExecute(props.portfolioId, {
      order_type: orderType.value,
      confirm: true,
    })
    emit('executed')
    emit('update:modelValue', false)
  } finally {
    executing.value = false
  }
}

watch(() => props.modelValue, (val) => {
  if (val) loadPlan()
})
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}
.mono {
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}
</style>
