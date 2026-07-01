<template>
  <div>
    <!-- Source filter chips -->
    <div class="d-flex align-center ga-2 mb-2">
      <v-chip
        :color="sourceFilter === 'all' ? 'primary' : 'default'"
        size="x-small"
        variant="flat"
        @click="sourceFilter = 'all'"
      >All ({{ allOrders.length }})</v-chip>
      <v-chip
        :color="sourceFilter === 'rebalance' ? 'primary' : 'default'"
        size="x-small"
        variant="flat"
        @click="sourceFilter = 'rebalance'"
      >Rebalance ({{ rebalanceOrders.length }})</v-chip>
      <v-chip
        :color="sourceFilter === 'broker' ? 'primary' : 'default'"
        size="x-small"
        variant="flat"
        @click="sourceFilter = 'broker'"
      >Broker ({{ brokerOrdersList.length }})</v-chip>
    </div>

    <!-- Empty state -->
    <div v-if="filteredOrders.length === 0" class="text-center py-6 text-medium-emphasis">
      {{ $t('portfolio.no_orders') }}
    </div>
    <template v-else>
      <!-- Bulk Action Toolbar (only for local rebalance orders) -->
      <div v-if="selectedIds.length > 0" class="bulk-bar d-flex align-center ga-2 pa-2 mb-2 rounded">
        <v-chip color="primary" size="small" variant="flat">{{ selectedIds.length }} selected</v-chip>
        <v-btn size="small" color="warning" variant="outlined" prepend-icon="mdi-cancel" @click="confirmBulkCancel">
          {{ $t('portfolio.cancel_selected') }}
        </v-btn>
        <v-btn size="small" color="info" variant="outlined" prepend-icon="mdi-swap-horizontal" @click="openBulkReplace">
          {{ $t('portfolio.replace_selected') }}
        </v-btn>
        <v-btn size="small" color="error" variant="outlined" prepend-icon="mdi-delete" @click="confirmBulkDelete">
          {{ $t('portfolio.delete_selected') }}
        </v-btn>
        <v-spacer />
        <v-btn size="x-small" variant="text" density="compact" @click="clearSelection">
          {{ $t('common.cancel') }}
        </v-btn>
      </div>

      <!-- Orders Table -->
      <v-table density="compact" class="orders-table">
        <thead>
          <tr>
            <th class="text-left" style="width:40px">
              <v-checkbox
                hide-details
                density="compact"
                :model-value="allSelected"
                :indeterminate="partialSelected"
                @update:model-value="toggleSelectAll"
                class="pa-0 ma-0"
              />
            </th>
            <th class="text-left" style="width:50px">{{ $t('portfolio.source') }}</th>
            <th class="text-left">#</th>
            <th class="text-left">{{ $t('common.symbol') }}</th>
            <th class="text-center">{{ $t('common.side') }}</th>
            <th class="text-center">{{ $t('common.type') }}</th>
            <th class="text-right">{{ $t('common.qty') }}</th>
            <th class="text-right">{{ $t('portfolio.target_value') }}</th>
            <th class="text-right">{{ $t('portfolio.filled_qty') }}</th>
            <th class="text-center">{{ $t('common.status') }}</th>
            <th class="text-left">{{ $t('portfolio.broker_order_id') }}</th>
            <th class="text-left">{{ $t('common.date') }}</th>
            <th class="text-center" style="width:60px">{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(o, i) in filteredOrders" :key="o._key" class="order-row" :class="{ 'row-selected': selectedIds.includes(o.id) }">
            <td>
              <v-checkbox
                v-if="o.source !== 'broker'"
                hide-details
                density="compact"
                :model-value="selectedIds.includes(o.id)"
                @update:model-value="toggleOne(o.id)"
                class="pa-0 ma-0"
              />
            </td>
            <td>
              <v-chip
                :color="o.source === 'broker' ? 'info' : 'primary'"
                size="x-small"
                variant="flat"
              >{{ o.source === 'broker' ? 'BKR' : 'RBL' }}</v-chip>
            </td>
            <td class="text-caption text-medium-emphasis">{{ i + 1 }}</td>
            <td><strong class="symbol-text">{{ o.symbol }}</strong></td>
            <td class="text-center">
              <v-chip :color="o.side === 'buy' ? 'success' : 'error'" size="x-small" variant="flat">
                {{ o.side.toUpperCase() }}
              </v-chip>
            </td>
            <td class="text-caption text-center">{{ o.order_type?.toUpperCase() || '—' }}</td>
            <td class="text-right mono">{{ displayQty(o) }}</td>
            <td class="text-right mono">{{ displayValue(o) }}</td>
            <td class="text-right mono">{{ Number(o.filled_qty || 0).toFixed(2) }}</td>
            <td class="text-center">
              <v-chip
                :color="statusColor(o.status)"
                size="x-small"
                variant="flat"
              >{{ o.status }}</v-chip>
            </td>
            <td class="text-caption text-medium-emphasis">{{ o.broker_order_id || '—' }}</td>
            <td class="text-caption">{{ formatTime(o.created_at) }}</td>
            <td class="text-center">
              <v-menu v-if="o.source !== 'broker'" location="bottom" offset="4">
                <template #activator="{ props }">
                  <v-btn v-bind="props" icon="mdi-dots-vertical" size="x-small" variant="text" density="compact" />
                </template>
                <v-list density="compact" class="action-menu">
                  <v-list-item
                    v-if="canCancel(o)"
                    prepend-icon="mdi-cancel"
                    @click="confirmCancelOne(o)"
                  >
                    {{ $t('portfolio.cancel_order') }}
                  </v-list-item>
                  <v-list-item
                    v-if="canReplace(o)"
                    prepend-icon="mdi-swap-horizontal"
                    @click="openReplaceDialog(o)"
                  >
                    {{ $t('portfolio.replace_order') }}
                  </v-list-item>
                  <v-list-item
                    v-if="canDelete(o)"
                    prepend-icon="mdi-delete"
                    class="text-error"
                    @click="confirmDeleteOne(o)"
                  >
                    {{ $t('common.delete') }}
                  </v-list-item>
                </v-list>
              </v-menu>
            </td>
          </tr>
        </tbody>
      </v-table>

      <!-- Footer -->
      <div class="text-caption text-medium-emphasis pa-3 border-t d-flex align-center ga-4">
        <span>{{ filteredOrders.length }} {{ $t('portfolio.orders_total') }}</span>
        <span v-if="sourceFilter === 'all'">· {{ groupedGroups.length }} {{ $t('portfolio.rebalance_runs') }}</span>
      </div>
    </template>

    <!-- ── Confirm Cancel Dialog ── -->
    <v-dialog v-model="showCancelConfirm" max-width="420">
      <v-card class="glass-dialog">
        <v-card-title class="text-warning">
          <v-icon start color="warning">mdi-alert</v-icon>
          {{ $t('portfolio.confirm_cancel_title') }}
        </v-card-title>
        <v-card-text>
          {{ $t('portfolio.confirm_cancel_msg', { count: pendingCancelItems.length }) }}
          <ul v-if="pendingCancelItems.length <= 5" class="mt-2">
            <li v-for="item in pendingCancelItems" :key="item.id">
              <strong>{{ item.symbol }}</strong> · {{ item.side.toUpperCase() }} · {{ displayQty(item) }}
            </li>
          </ul>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showCancelConfirm = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="warning" variant="flat" @click="doCancel" :loading="cancelling">
            {{ $t('portfolio.confirm_cancel_btn') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ── Replace Dialog ── -->
    <v-dialog v-model="showReplace" max-width="480">
      <v-card class="glass-dialog">
        <v-card-title>
          <v-icon start>mdi-swap-horizontal</v-icon>
          {{ $t('portfolio.replace_order_title') }}
        </v-card-title>
        <v-card-text>
          <div v-if="replaceTarget" class="mb-3 text-caption text-medium-emphasis">
            {{ replaceTarget.symbol }} · {{ replaceTarget.side.toUpperCase() }} · {{ displayQty(replaceTarget) }}
          </div>
          <v-select
            v-model="replaceForm.type"
            :label="$t('portfolio.new_order_type')"
            :items="orderTypeOptions"
            item-title="text"
            item-value="value"
            variant="outlined"
            density="compact"
            hide-details
            class="mb-3"
          />
          <v-text-field
            v-if="replaceForm.type === 'limit'"
            v-model="replaceForm.price"
            :label="$t('portfolio.new_limit_price')"
            type="number"
            step="0.01"
            min="0"
            variant="outlined"
            density="compact"
            hide-details
            :placeholder="$t('portfolio.price_placeholder')"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showReplace = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" variant="flat" @click="doReplace" :loading="replacing">
            {{ $t('portfolio.replace_confirm_btn') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ── Confirm Delete Dialog ── -->
    <v-dialog v-model="showDeleteConfirm" max-width="420">
      <v-card class="glass-dialog">
        <v-card-title class="text-error">
          <v-icon start color="error">mdi-delete</v-icon>
          {{ $t('portfolio.confirm_delete_title') }}
        </v-card-title>
        <v-card-text>
          {{ $t('portfolio.confirm_delete_msg', { count: pendingDeleteItems.length }) }}
          <ul v-if="pendingDeleteItems.length <= 5" class="mt-2">
            <li v-for="item in pendingDeleteItems" :key="item.id">
              <strong>{{ item.symbol }}</strong> · {{ item.status }}
            </li>
          </ul>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeleteConfirm = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" variant="flat" @click="doDelete" :loading="deleting">
            {{ $t('common.delete') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ── Error Snackbar ── -->
    <v-snackbar v-model="showError" color="error" timeout="5000">
      {{ errorMsg }}
      <template #actions>
        <v-btn variant="text" @click="showError = false">{{ $t('common.cancel') }}</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { usePortfolioStore } from '@/stores/portfolioStore'

const props = defineProps({
  orders: { type: Array, default: () => [] },
  brokerOrders: { type: Array, default: () => [] },
})

const emit = defineEmits(['refreshed'])

const store = usePortfolioStore()
const sourceFilter = ref('all')

// ── Merge local + broker orders ─────────────────────────

const rebalanceOrders = computed(() => {
  return (props.orders || []).map(o => ({
    ...o,
    _key: `rbl_${o.id}`,
    source: 'rebalance',
    order_type: o.order_type,
    qty: o.target_qty,
  }))
})

const brokerOrdersList = computed(() => {
  return (props.brokerOrders || []).map(o => ({
    ...o,
    _key: `bkr_${o.id}`,
    source: 'broker',
    order_type: o.order_type || 'market',
    // Map broker fields to match local schema
    target_qty: o.qty,
    target_value: o.qty * o.price || 0,
    limit_price: o.price || null,
    avg_fill_price: o.avg_fill_price || 0,
    filled_value: o.filled_qty * o.avg_fill_price || 0,
    error_message: null,
    rebalance_group_id: null,
    retry_count: 0,
    user_id: null,
    org_id: null,
    portfolio_id: null,
  }))
})

const allOrders = computed(() => {
  return [...rebalanceOrders.value, ...brokerOrdersList.value]
})

const filteredOrders = computed(() => {
  if (sourceFilter.value === 'all') return allOrders.value
  return allOrders.value.filter(o => o.source === sourceFilter.value)
})

// ── Display helpers for mixed formats ───────────────────

function displayQty(o) {
  const q = Number(o.qty || o.target_qty || 0)
  return q.toFixed(2)
}

function displayValue(o) {
  const v = Number(o.target_value || o.qty * o.price || 0)
  return '$' + v.toLocaleString(undefined, { minimumFractionDigits: 2 })
}

// ── Selection State ─────────────────────────────────────

const selectedIds = ref([])

const allSelected = computed(() => {
  const selectable = filteredOrders.value.filter(o => o.source !== 'broker')
  return selectable.length > 0 && selectedIds.value.length === selectable.length
})

const partialSelected = computed(() => {
  return selectedIds.value.length > 0 && !allSelected.value
})

function toggleSelectAll(val) {
  if (val) {
    selectedIds.value = filteredOrders.value.filter(o => o.source !== 'broker').map(o => o.id)
  } else {
    selectedIds.value = []
  }
}

function toggleOne(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx === -1) {
    selectedIds.value.push(id)
  } else {
    selectedIds.value.splice(idx, 1)
  }
}

function clearSelection() {
  selectedIds.value = []
}

// ── Grouping ────────────────────────────────────────────

const groupedGroups = computed(() => {
  const groups = new Set()
  for (const o of rebalanceOrders.value) {
    if (o.rebalance_group_id) groups.add(o.rebalance_group_id)
  }
  return [...groups]
})

// ── Status Helpers ──────────────────────────────────────

function statusColor(status) {
  const map = {
    pending: 'warning',
    submitted: 'info',
    partially_filled: 'primary',
    filled: 'success',
    completed: 'success',
    cancelled: 'grey',
    canceled: 'grey',
    rejected: 'error',
    failed: 'error',
  }
  return map[status?.toLowerCase()] || 'grey'
}

function isOpen(status) {
  const s = (status || '').toLowerCase()
  return s === 'pending' || s === 'submitted' || s === 'partially_filled' || s === 'new'
}

function canCancel(o) {
  return true  // Any order can be cancelled (locally marked; broker cancel attempted if linked)
}

function canReplace(o) {
  return o.broker_order_id && isOpen(o.status)
}

function canDelete(o) {
  return true  // Any order can be deleted from local DB
}

// ── Cancel Logic ────────────────────────────────────────

const showCancelConfirm = ref(false)
const pendingCancelItems = ref([])
const cancelling = ref(false)

function confirmCancelOne(order) {
  pendingCancelItems.value = [order]
  showCancelConfirm.value = true
}

function confirmBulkCancel() {
  const items = filteredOrders.value.filter(o => selectedIds.value.includes(o.id) && o.source !== 'broker')
  if (items.length === 0) {
    errorMsg.value = 'No cancelable orders selected'
    showError.value = true
    return
  }
  pendingCancelItems.value = items
  showCancelConfirm.value = true
}

async function doCancel() {
  cancelling.value = true
  try {
    const ids = pendingCancelItems.value.map(o => o.id)
    const portfolioId = pendingCancelItems.value[0]?.portfolio_id
    if (!portfolioId) throw new Error('No portfolio ID')
    await store.bulkCancelOrders(portfolioId, ids)
    showCancelConfirm.value = false
    pendingCancelItems.value = []
    clearSelection()
    emit('refreshed')
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || e.message || 'Cancel failed'
    showError.value = true
  } finally {
    cancelling.value = false
  }
}

// ── Replace Logic ───────────────────────────────────────

const showReplace = ref(false)
const replaceTarget = ref(null)
const replaceForm = ref({ type: 'market', price: null })
const replacing = ref(false)

const orderTypeOptions = [
  { text: 'Market', value: 'market' },
  { text: 'Limit', value: 'limit' },
]

function openReplaceDialog(order) {
  replaceTarget.value = order
  replaceForm.value = {
    type: order.order_type || 'market',
    price: order.limit_price ? Number(order.limit_price).toFixed(2) : null,
  }
  showReplace.value = true
}

function openBulkReplace() {
  const first = filteredOrders.value.find(o => selectedIds.value.includes(o.id) && canReplace(o))
  if (!first) {
    errorMsg.value = 'No replaceable orders selected'
    showError.value = true
    return
  }
  openReplaceDialog(first)
}

async function doReplace() {
  if (!replaceTarget.value) return
  replacing.value = true
  try {
    const payload = {
      new_order_type: replaceForm.value.type,
    }
    if (replaceForm.value.type === 'limit' && replaceForm.value.price) {
      payload.new_limit_price = parseFloat(replaceForm.value.price)
    }
    await store.replaceOrder(replaceTarget.value.portfolio_id, replaceTarget.value.id, payload)
    showReplace.value = false
    replaceTarget.value = null
    clearSelection()
    emit('refreshed')
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || e.message || 'Replace failed'
    showError.value = true
  } finally {
    replacing.value = false
  }
}

// ── Delete Logic ────────────────────────────────────────

const showDeleteConfirm = ref(false)
const pendingDeleteItems = ref([])
const deleting = ref(false)

function confirmDeleteOne(order) {
  if (order.source === 'broker') return  // Cannot delete broker orders from local DB
  pendingDeleteItems.value = [order]
  showDeleteConfirm.value = true
}

function confirmBulkDelete() {
  const items = filteredOrders.value.filter(o => selectedIds.value.includes(o.id) && o.source !== 'broker')
  if (items.length === 0) {
    errorMsg.value = 'No deletable orders selected'
    showError.value = true
    return
  }
  pendingDeleteItems.value = items
  showDeleteConfirm.value = true
}

async function doDelete() {
  deleting.value = true
  try {
    const ids = pendingDeleteItems.value.map(o => o.id)
    const portfolioId = pendingDeleteItems.value[0]?.portfolio_id
    if (!portfolioId) throw new Error('No portfolio ID')
    await store.bulkDeleteOrders(portfolioId, ids)
    showDeleteConfirm.value = false
    pendingDeleteItems.value = []
    clearSelection()
    emit('refreshed')
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || e.message || 'Delete failed'
    showError.value = true
  } finally {
    deleting.value = false
  }
}

// ── Misc ─────────────────────────────────────────────────

const showError = ref(false)
const errorMsg = ref('')

function formatTime(d) {
  if (!d) return '—'
  const dt = new Date(d)
  if (isNaN(dt.getTime())) return d
  return dt.toLocaleDateString() + ' ' + dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.orders-table {
  width: 100%;
}
.order-row:hover td {
  background: rgba(255,255,255,0.02);
}
.row-selected td {
  background: rgba(33, 150, 243, 0.06);
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
.bulk-bar {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
}
.action-menu {
  background: rgba(30, 30, 40, 0.98) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.08);
}
</style>
