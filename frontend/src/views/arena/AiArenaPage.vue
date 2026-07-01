<template>
  <div>
    <!-- Header -->
    <v-row>
      <v-col cols="12" class="d-flex align-center justify-space-between flex-wrap">
        <div>
          <h2 class="text-h4 font-weight-bold">
            <v-icon large color="primary" class="mr-2">mdi-robot</v-icon>
            AI Manager Arena
          </h2>
          <p class="text-medium-emphasis">Let different AI fund managers compete and compare their performance</p>
        </div>
        <div class="d-flex ga-2 mt-2">
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            @click="showAddDialog = true"
          >
            {{ $t('arena.add_manager') }}
          </v-btn>
          <v-btn
            color="warning"
            variant="outlined"
            prepend-icon="mdi-play-all"
            :loading="arenaStore.triggering"
            @click="runAll"
          >
            {{ $t('arena.run_all') }}
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Error Alert -->
    <v-alert
      v-if="arenaStore.error"
      type="error"
      density="compact"
      variant="tonal"
      closable
      class="mb-3"
      @click:close="arenaStore.error = null"
    >{{ arenaStore.error }}</v-alert>

    <!-- Stats Bar -->
    <v-row class="mt-2">
      <v-col cols="12" md="3">
        <v-card class="glass-card pa-3" elevation="0">
          <div class="text-caption text-medium-emphasis">{{ $t('arena.total_managers') }}</div>
          <div class="text-h5 font-weight-bold">{{ arenaStore.managers.length }}</div>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card class="glass-card pa-3" elevation="0">
          <div class="text-caption text-medium-emphasis">{{ $t('arena.active_managers') }}</div>
          <div class="text-h5 font-weight-bold text-success">{{ arenaStore.activeManagers.length }}</div>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card class="glass-card pa-3" elevation="0">
          <div class="text-caption text-medium-emphasis">{{ $t('arena.total_decisions') }}</div>
          <div class="text-h5 font-weight-bold">
            {{ totalDecisions }}
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card class="glass-card pa-3" elevation="0">
          <div class="text-caption text-medium-emphasis">{{ $t('arena.top_performer') }}</div>
          <div class="text-h6 font-weight-bold text-primary" v-if="topManager">
            {{ topManager.name }}
            <v-chip size="x-small" color="success" variant="flat" class="ml-1">
              +{{ topManager.total_return_pct.toFixed(1) }}%
            </v-chip>
          </div>
          <div v-else class="text-medium-emphasis text-body-2">--</div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Leaderboard -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card class="glass-card" elevation="0">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" color="warning">mdi-podium-gold</v-icon>
            {{ $t('arena.leaderboard') }}
            <v-spacer />
            <v-btn
              size="small"
              variant="text"
              icon="mdi-refresh"
              @click="refreshAll"
              :loading="arenaStore.loading"
            />
          </v-card-title>
          <v-card-text>
            <LeaderboardTable
              :entries="arenaStore.leaderboard"
              :triggering-id="triggeringId"
              @trigger="onTrigger"
              @view-logs="onViewLogs"
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Comparison Chart -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card class="glass-card" elevation="0">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" color="info">mdi-chart-timeline-variant</v-icon>
            {{ $t('arena.comparison_chart') }}
          </v-card-title>
          <v-card-text>
            <ComparisonChart :series="arenaStore.comparisonSeries" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Decision Log Panel -->
    <v-row class="mt-4" v-if="selectedManagerId">
      <v-col cols="12">
        <v-card class="glass-card" elevation="0">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" color="primary">mdi-chart-timeline-variant</v-icon>
            {{ $t('arena.decision_history') }}
            <v-chip size="small" variant="flat" class="ml-2" color="primary">
              {{ selectedManagerName }}
            </v-chip>
            <v-spacer />
            <v-btn size="small" variant="text" icon="mdi-close" @click="selectedManagerId = null" />
          </v-card-title>
          <v-card-text>
            <div v-if="decisionLogs.length === 0" class="text-center py-4 text-medium-emphasis">
              {{ $t('arena.no_decisions') }}
            </div>
            <div v-else class="decision-timeline">
              <div v-for="log in decisionLogs" :key="log.id" class="decision-item pa-3 mb-2 rounded">
                <div class="d-flex align-center justify-space-between">
                  <div class="d-flex align-center ga-2">
                    <v-icon size="small" color="primary">mdi-robot</v-icon>
                    <strong class="text-body-2">{{ log.trigger_source }}</strong>
                    <v-chip
                      :color="statusColor(log.execution_status)"
                      size="x-small"
                      variant="flat"
                    >{{ log.execution_status }}</v-chip>
                  </div>
                  <div class="text-caption text-medium-emphasis">{{ formatTime(log.triggered_at) }}</div>
                </div>
                <div class="mt-1 text-body-2 text-medium-emphasis" v-if="log.reasoning">
                  {{ log.reasoning.substring(0, 200) }}...
                </div>
                <div class="mt-1 d-flex ga-2" v-if="log.portfolio_snapshot_before">
                  <v-chip size="x-small" variant="text">
                    Orders: {{ log.orders_created || 0 }}
                  </v-chip>
                  <v-chip size="x-small" variant="text" v-if="log.market_regime">
                    Regime: {{ log.market_regime }}
                  </v-chip>
                </div>
              </div>
            </div>
            <div v-if="decisionLogs.length >= 20" class="text-center text-caption text-medium-emphasis mt-2">
              Showing last 20 decisions
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialogs -->
    <AddAiManagerDialog v-model="showAddDialog" @created="onCreated" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useArenaStore } from '@/stores/arenaStore'
import LeaderboardTable from '@/components/arena/LeaderboardTable.vue'
import ComparisonChart from '@/components/arena/ComparisonChart.vue'
import AddAiManagerDialog from '@/components/arena/AddAiManagerDialog.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const arenaStore = useArenaStore()

const showAddDialog = ref(false)
const selectedManagerId = ref(null)
const selectedManagerName = ref('')
const triggeringId = ref(null)
const decisionLogs = ref([])

const totalDecisions = computed(() =>
  arenaStore.leaderboard.reduce((sum, e) => sum + (e.decisions_count || 0), 0)
)

const topManager = computed(() => arenaStore.leaderboard[0] || null)

function formatTime(d) {
  if (!d) return ''
  const dt = new Date(d)
  if (isNaN(dt.getTime())) return d
  return dt.toLocaleDateString() + ' ' + dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function statusColor(status) {
  const map = {
    pending_review: 'warning',
    executed: 'success',
    rejected: 'error',
    failed: 'error',
  }
  return map[status] || 'grey'
}

async function onTrigger(managerId) {
  triggeringId.value = managerId
  try {
    await arenaStore.triggerDecision(managerId)
    await arenaStore.fetchComparisonChart()
  } finally {
    triggeringId.value = null
  }
}

async function onViewLogs(managerId) {
  selectedManagerId.value = managerId
  const mgr = arenaStore.managers.find(m => m.id === managerId)
  selectedManagerName.value = mgr?.name || `#${managerId}`
  const logs = await arenaStore.fetchDecisionLogs(managerId)
  decisionLogs.value = logs || []
}

async function runAll() {
  await arenaStore.triggerAll()
  await arenaStore.fetchComparisonChart()
}

async function refreshAll() {
  await Promise.all([
    arenaStore.fetchLeaderboard(),
    arenaStore.fetchComparisonChart(),
    arenaStore.fetchManagers(),
  ])
  // Refresh decision logs if panel is open
  if (selectedManagerId.value) {
    const logs = await arenaStore.fetchDecisionLogs(selectedManagerId.value)
    decisionLogs.value = logs || []
  }
}

function onCreated() {
  refreshAll()
}

onMounted(() => {
  refreshAll()
})

// Watch for decision logs store updates
watch(() => arenaStore.decisionLogs, (logs) => {
  if (selectedManagerId.value) {
    decisionLogs.value = logs || []
  }
}, { immediate: true })
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}
.decision-item {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  transition: background 0.2s;
}
.decision-item:hover {
  background: rgba(255, 255, 255, 0.04);
}
</style>
