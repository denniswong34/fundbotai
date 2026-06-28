<template>
  <div v-if="portfolio">
    <!-- Header -->
    <v-row>
      <v-col cols="12" class="d-flex align-center justify-space-between flex-wrap">
        <div>
          <v-btn variant="text" prepend-icon="mdi-arrow-left" class="mb-2" @click="$router.push('/portfolios')">
            {{ $t('common.back') }}
          </v-btn>
          <h2 class="text-h4 font-weight-bold">{{ portfolio.name }}</h2>
          <div class="text-medium-emphasis" v-if="portfolio.description">{{ portfolio.description }}</div>
        </div>
        <div class="d-flex ga-2 mt-2">
          <v-btn color="primary" variant="outlined" prepend-icon="mdi-sync" @click="doSync" :loading="syncing">
            {{ $t('common.sync') }}
          </v-btn>
          <v-btn color="warning" prepend-icon="mdi-chart-arcs" @click="openRebalance">
            {{ $t('portfolio.rebalance') }}
          </v-btn>
          <v-btn color="primary" variant="text" prepend-icon="mdi-pencil" @click="showEdit = true">
            {{ $t('portfolio.edit') }}
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Stats Row -->
    <v-row class="mt-2">
      <v-col cols="12" md="3">
        <v-card class="glass-card pa-3" elevation="0">
          <div class="text-caption text-medium-emphasis">{{ $t('portfolio.total_value') }}</div>
          <div class="text-h5 font-weight-bold">{{ formatCurrency(portfolio.total_value) }}</div>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card class="glass-card pa-3" elevation="0">
          <div class="text-caption text-medium-emphasis">{{ $t('portfolio.total_pnl') }}</div>
          <div class="text-h5 font-weight-bold" :class="pnlColor">
            {{ formatCurrency(portfolio.total_pnl) }}
            <span class="text-body-2">({{ Number(portfolio.total_pnl_pct).toFixed(2) }}%)</span>
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card class="glass-card pa-3" elevation="0">
          <div class="text-caption text-medium-emphasis">{{ $t('common.last_rebalanced') }}</div>
          <div class="text-h6" v-if="portfolio.last_rebalanced_at">{{ formatDate(portfolio.last_rebalanced_at) }}</div>
          <div class="text-h6 text-medium-emphasis" v-else>--</div>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card class="glass-card pa-3" elevation="0">
          <div class="text-caption text-medium-emphasis">{{ $t('common.currency') }}</div>
          <div class="text-h6">{{ portfolio.base_currency }}</div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Allocation Pie & Holdings -->
    <v-row class="mt-4">
      <v-col cols="12" md="5">
        <v-card class="glass-card" elevation="0">
          <v-card-title>{{ $t('portfolio.allocation') }}</v-card-title>
          <v-card-text>
            <AllocationPieChart :data="allocation" />
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="7">
        <v-card class="glass-card" elevation="0">
          <v-card-title class="d-flex align-center">
            {{ $t('portfolio.holdings') }}
            <v-spacer />
            <v-btn size="small" color="primary" variant="outlined" prepend-icon="mdi-plus" @click="showAddHolding = true">
              {{ $t('portfolio.add_holding') }}
            </v-btn>
          </v-card-title>
          <v-card-text>
            <DriftAnalysisBar :holdings="holdings" />
            <HoldingsTable
              :holdings="holdings"
              @update="onUpdateHolding"
              @delete="onRemoveHolding"
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Performance Chart -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card class="glass-card" elevation="0">
          <v-card-title>{{ $t('portfolio.performance') }}</v-card-title>
          <v-card-text>
            <PerformanceChart :data="performance" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialogs -->
    <CreatePortfolioDialog v-model="showEdit" :portfolio="portfolio" @updated="onUpdated" />
    <RebalanceDialog
      v-model="showRebalance"
      :portfolio-id="portfolio.id"
      @executed="onRebalanceExecuted"
    />
    <AddHoldingDialog v-model="showAddHolding" :portfolio-id="portfolio.id" @added="onHoldingAdded" />
  </div>
  <div v-else-if="loading" class="text-center py-8">
    <v-progress-circular indeterminate color="primary" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { usePortfolioStore } from '@/stores/portfolioStore'
import AllocationPieChart from '@/components/portfolio/AllocationPieChart.vue'
import HoldingsTable from '@/components/portfolio/HoldingsTable.vue'
import DriftAnalysisBar from '@/components/portfolio/DriftAnalysisBar.vue'
import PerformanceChart from '@/components/portfolio/PerformanceChart.vue'
import CreatePortfolioDialog from '@/components/portfolio/CreatePortfolioDialog.vue'
import RebalanceDialog from '@/components/portfolio/RebalanceDialog.vue'
import AddHoldingDialog from '@/components/portfolio/AddHoldingDialog.vue'

const route = useRoute()
const portfolioStore = usePortfolioStore()

const portfolioId = Number(route.params.id)
const showEdit = ref(false)
const showRebalance = ref(false)
const showAddHolding = ref(false)
const syncing = ref(false)

const portfolio = computed(() => portfolioStore.currentPortfolio)
const holdings = computed(() => portfolioStore.holdings)
const allocation = computed(() => portfolioStore.allocation)
const performance = computed(() => portfolioStore.performance)
const loading = computed(() => portfolioStore.loading)

const pnlColor = computed(() => {
  return Number(portfolio.value?.total_pnl || 0) >= 0 ? 'text-success' : 'text-error'
})

function formatCurrency(val) {
  const num = Number(val || 0)
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(num)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}

async function doSync() {
  syncing.value = true
  try {
    await portfolioStore.syncPortfolio(portfolioId)
    await Promise.all([
      portfolioStore.fetchPortfolio(portfolioId),
      portfolioStore.fetchHoldings(portfolioId),
      portfolioStore.fetchAllocation(portfolioId),
    ])
  } finally {
    syncing.value = false
  }
}

function openRebalance() {
  showRebalance.value = true
}

function onUpdated() {
  portfolioStore.fetchPortfolio(portfolioId)
}

function onRebalanceExecuted() {
  Promise.all([
    portfolioStore.fetchPortfolio(portfolioId),
    portfolioStore.fetchHoldings(portfolioId),
    portfolioStore.fetchAllocation(portfolioId),
    portfolioStore.fetchPerformance(portfolioId),
  ])
}

async function onUpdateHolding({ holdingId, data }) {
  await portfolioStore.updateHolding(portfolioId, holdingId, data)
  await Promise.all([
    portfolioStore.fetchPortfolio(portfolioId),
    portfolioStore.fetchAllocation(portfolioId),
  ])
}

async function onRemoveHolding(holdingId) {
  await portfolioStore.removeHolding(portfolioId, holdingId)
  await Promise.all([
    portfolioStore.fetchPortfolio(portfolioId),
    portfolioStore.fetchAllocation(portfolioId),
  ])
}

function onHoldingAdded() {
  portfolioStore.fetchHoldings(portfolioId)
  portfolioStore.fetchAllocation(portfolioId)
}

onMounted(async () => {
  await portfolioStore.fetchPortfolio(portfolioId)
  await Promise.all([
    portfolioStore.fetchHoldings(portfolioId),
    portfolioStore.fetchAllocation(portfolioId),
    portfolioStore.fetchPerformance(portfolioId),
  ])
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
