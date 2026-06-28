<template>
  <div>
    <v-table density="compact" class="holdings-table">
      <thead>
        <tr>
          <th class="text-left">{{ $t('common.symbol') }}</th>
          <th class="text-right">{{ $t('portfolio.target_weight') }}</th>
          <th class="text-right">{{ $t('portfolio.current_weight') }}</th>
          <th class="text-right">{{ $t('common.shares') }}</th>
          <th class="text-right">{{ $t('common.price') }}</th>
          <th class="text-right">{{ $t('portfolio.market_value') }}</th>
          <th class="text-right">{{ $t('portfolio.unrealized_pnl') }}</th>
          <th class="text-center">{{ $t('portfolio.drift') }}</th>
          <th class="text-center">{{ $t('common.actions') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="h in holdings" :key="h.id">
          <td>
            <strong>{{ h.symbol }}</strong>
            <span class="text-caption text-medium-emphasis ml-1">{{ h.market }}</span>
          </td>
          <td class="text-right font-weight-bold">{{ Number(h.target_weight_pct).toFixed(2) }}%</td>
          <td class="text-right">{{ Number(h.current_weight_pct).toFixed(2) }}%</td>
          <td class="text-right mono">{{ Number(h.current_shares).toLocaleString(undefined, { maximumFractionDigits: 2 }) }}</td>
          <td class="text-right mono">{{ formatCurrency(h.current_price) }}</td>
          <td class="text-right mono">{{ formatCurrency(h.market_value) }}</td>
          <td class="text-right mono" :class="Number(h.unrealized_pnl) >= 0 ? 'text-success' : 'text-error'">
            {{ Number(h.unrealized_pnl) >= 0 ? '+' : '' }}{{ formatCurrency(h.unrealized_pnl) }}
          </td>
          <td class="text-center">
            <v-chip
              :color="getDriftColor(h)"
              size="x-small"
              variant="flat"
              class="px-1"
            >
              {{ getDriftText(h) }}
            </v-chip>
          </td>
          <td class="text-center">
            <v-btn icon size="x-small" variant="text" @click="editHolding(h)">
              <v-icon small>mdi-pencil</v-icon>
            </v-btn>
            <v-btn icon size="x-small" variant="text" color="error" @click="$emit('delete', h.id)">
              <v-icon small>mdi-delete</v-icon>
            </v-btn>
          </td>
        </tr>
        <tr v-if="holdings.length === 0">
          <td colspan="9" class="text-center text-medium-emphasis py-4">
            {{ $t('common.no_data') }}
          </td>
        </tr>
      </tbody>
    </v-table>

    <!-- Edit Holding Dialog -->
    <v-dialog v-model="editDialog" max-width="500">
      <v-card class="glass-card">
        <v-card-title>{{ $t('portfolio.edit_holding') }}: {{ editingHolding?.symbol }}</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editForm.target_weight_pct"
            :label="$t('portfolio.target_weight')"
            type="number"
            suffix="%"
            variant="outlined"
            density="compact"
            class="mb-3"
          />
          <v-text-field
            v-model="editForm.current_shares"
            :label="$t('common.shares')"
            type="number"
            variant="outlined"
            density="compact"
            class="mb-3"
          />
          <v-text-field
            v-model="editForm.current_price"
            :label="$t('common.price')"
            type="number"
            variant="outlined"
            density="compact"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="editDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" @click="saveEdit">{{ $t('common.save') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  holdings: { type: Array, default: () => [] },
})

const emit = defineEmits(['update', 'delete'])

const editDialog = ref(false)
const editingHolding = ref(null)
const editForm = ref({})

function formatCurrency(val) {
  const num = Number(val || 0)
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(num)
}

function getDriftColor(h) {
  const drift = Math.abs(Number(h.drift_pct || 0))
  const threshold = 5 // default threshold
  if (drift <= threshold * 0.5) return 'success'
  if (drift <= threshold) return 'warning'
  return 'error'
}

function getDriftText(h) {
  const drift = Number(h.drift_pct || 0)
  const abs = Math.abs(drift)
  return `${drift >= 0 ? '+' : ''}${abs.toFixed(2)}%`
}

function editHolding(h) {
  editingHolding.value = h
  editForm.value = {
    target_weight_pct: Number(h.target_weight_pct),
    current_shares: Number(h.current_shares),
    current_price: Number(h.current_price),
  }
  editDialog.value = true
}

function saveEdit() {
  if (!editingHolding.value) return
  emit('update', {
    holdingId: editingHolding.value.id,
    data: { ...editForm.value },
  })
  editDialog.value = false
}
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}
.holdings-table :deep(td) {
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}
.holdings-table :deep(th) {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(255, 255, 255, 0.5);
}
.mono {
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}
</style>
