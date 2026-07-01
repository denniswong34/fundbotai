<template>
  <div>
    <!-- Source filter -->
    <div class="d-flex align-center ga-2 mb-2">
      <v-chip
        :color="sourceFilter === 'all' ? 'primary' : 'default'"
        size="x-small"
        variant="flat"
        @click="sourceFilter = 'all'"
      >All ({{ allTrades.length }})</v-chip>
      <v-chip
        :color="sourceFilter === 'rebalance' ? 'primary' : 'default'"
        size="x-small"
        variant="flat"
        @click="sourceFilter = 'rebalance'"
      >Rebalance ({{ rebalanceTrades.length }})</v-chip>
      <v-chip
        :color="sourceFilter === 'broker' ? 'primary' : 'default'"
        size="x-small"
        variant="flat"
        @click="sourceFilter = 'broker'"
      >Broker ({{ brokerTradesList.length }})</v-chip>
    </div>

    <div v-if="filteredTrades.length === 0" class="text-center py-6 text-medium-emphasis">
      {{ $t('portfolio.no_trades') }}
    </div>
    <template v-else>
      <v-table density="compact" class="trades-table">
        <thead>
          <tr>
            <th class="text-left" style="width:50px">{{ $t('portfolio.source') }}</th>
            <th class="text-left">#</th>
            <th class="text-left">{{ $t('common.symbol') }}</th>
            <th class="text-center">{{ $t('common.side') }}</th>
            <th class="text-right">{{ $t('portfolio.filled_qty') }}</th>
            <th class="text-right">{{ $t('portfolio.avg_fill_price') }}</th>
            <th class="text-right">{{ $t('portfolio.filled_value') }}</th>
            <th class="text-left">{{ $t('portfolio.broker_order_id') }}</th>
            <th class="text-left">{{ $t('common.date') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(t, i) in filteredTrades" :key="t._key" class="trade-row">
            <td>
              <v-chip
                :color="t.source === 'broker' ? 'info' : 'primary'"
                size="x-small"
                variant="flat"
              >{{ t.source === 'broker' ? 'BKR' : 'RBL' }}</v-chip>
            </td>
            <td class="text-caption text-medium-emphasis">{{ i + 1 }}</td>
            <td><strong class="symbol-text">{{ t.symbol }}</strong></td>
            <td class="text-center">
              <v-chip :color="t.side === 'buy' ? 'success' : 'error'" size="x-small" variant="flat">
                {{ t.side.toUpperCase() }}
              </v-chip>
            </td>
            <td class="text-right mono">{{ Number(t.filled_qty || 0).toFixed(2) }}</td>
            <td class="text-right mono">${{ Number(t.avg_fill_price || 0).toFixed(2) }}</td>
            <td class="text-right mono">${{ filledValue(t).toLocaleString(undefined, {minimumFractionDigits:2}) }}</td>
            <td class="text-caption text-medium-emphasis">{{ t.broker_order_id || '—' }}</td>
            <td class="text-caption">{{ formatTime(t.created_at) }}</td>
          </tr>
        </tbody>
      </v-table>
      <div class="text-caption text-medium-emphasis pa-3 border-t">
        {{ filteredTrades.length }} {{ $t('portfolio.trades_completed') }}
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  orders: { type: Array, default: () => [] },
  brokerTrades: { type: Array, default: () => [] },
})

const sourceFilter = ref('all')

// ── Merge local filled orders + broker trades ───────────

const rebalanceTrades = computed(() => {
  return (props.orders || [])
    .filter(o => {
      const s = (o.status || '').toLowerCase()
      return s === 'filled' || s === 'completed'
    })
    .map(o => ({
      ...o,
      _key: `rbl_${o.id}`,
      source: 'rebalance',
    }))
})

const brokerTradesList = computed(() => {
  return (props.brokerTrades || []).map(o => ({
    ...o,
    _key: `bkr_${o.id}`,
    source: 'broker',
    // Normalize
    symbol: o.symbol,
    side: o.side,
    filled_qty: o.filled_qty,
    avg_fill_price: o.avg_fill_price || o.price || 0,
    filled_value: o.filled_qty * (o.avg_fill_price || o.price || 0),
    broker_order_id: o.broker_order_id,
    created_at: o.created_at,
  }))
})

const allTrades = computed(() => {
  return [...rebalanceTrades.value, ...brokerTradesList.value]
})

const filteredTrades = computed(() => {
  if (sourceFilter.value === 'all') return allTrades.value
  return allTrades.value.filter(t => t.source === sourceFilter.value)
})

function filledValue(t) {
  return Number(t.filled_value || t.filled_qty * t.avg_fill_price || 0)
}

function formatTime(d) {
  if (!d) return '—'
  const dt = new Date(d)
  if (isNaN(dt.getTime())) return d
  return dt.toLocaleDateString() + ' ' + dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.trades-table {
  width: 100%;
}
.trade-row:hover td {
  background: rgba(255,255,255,0.02);
}
.symbol-text {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 13px;
}
.mono {
  font-family: 'SF Mono', 'Fira Code', monospace;
}
.border-t {
  border-top: 1px solid rgba(255,255,255,0.06);
}
</style>
