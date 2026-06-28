<template>
  <div>
    <v-row>
      <v-col cols="12">
        <h2 class="text-h4 font-weight-bold mb-2">{{ $t('nav.dashboard') }}</h2>
        <p class="text-medium-emphasis mb-6">{{ $t('common.welcome') }}, {{ auth.user?.username || 'User' }}</p>
      </v-col>
    </v-row>

    <!-- Stats Cards -->
    <v-row>
      <v-col cols="12" md="3">
        <v-card class="glass-card pa-4" elevation="0">
          <v-card-text class="text-center">
            <v-icon size="36" color="primary" class="mb-2">mdi-briefcase-variant</v-icon>
            <div class="text-h5 font-weight-bold">{{ summary?.total_portfolios || 0 }}</div>
            <div class="text-caption text-medium-emphasis">{{ $t('portfolio.title') }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card class="glass-card pa-4" elevation="0">
          <v-card-text class="text-center">
            <v-icon size="36" color="primary" class="mb-2">mdi-currency-usd</v-icon>
            <div class="text-h5 font-weight-bold">{{ formatCurrency(summary?.total_value || 0) }}</div>
            <div class="text-caption text-medium-emphasis">{{ $t('portfolio.total_value') }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card class="glass-card pa-4" elevation="0">
          <v-card-text class="text-center">
            <v-icon size="36" :color="pnlColor" class="mb-2">mdi-trending-up</v-icon>
            <div class="text-h5 font-weight-bold" :class="pnlColor">{{ formatCurrency(summary?.total_pnl || 0) }}</div>
            <div class="text-caption text-medium-emphasis">{{ $t('portfolio.total_pnl') }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card class="glass-card pa-4" elevation="0">
          <v-card-text class="text-center">
            <v-icon size="36" color="primary" class="mb-2">mdi-chart-pie</v-icon>
            <div class="text-h5 font-weight-bold">{{ summary?.active_count || 0 }}</div>
            <div class="text-caption text-medium-emphasis">Active</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Quick Actions -->
    <v-row class="mt-4">
      <v-col cols="12" md="6">
        <v-card class="glass-card" elevation="0">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-lightning-bolt</v-icon>
            {{ $t('common.quick_actions') }}
          </v-card-title>
          <v-card-text>
            <v-btn color="primary" class="mr-3 mb-2" prepend-icon="mdi-plus" @click="showCreateDialog = true">
              {{ $t('portfolio.create') }}
            </v-btn>
            <v-btn color="secondary" class="mb-2" prepend-icon="mdi-link-variant" @click="$router.push('/brokers')">
              {{ $t('common.connect_broker') }}
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <v-card class="glass-card" elevation="0">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-clock-outline</v-icon>
            {{ $t('common.recent') }}
          </v-card-title>
          <v-card-text>
            <v-list v-if="portfolios.length > 0" density="compact">
              <v-list-item
                v-for="p in portfolios.slice(0, 5)"
                :key="p.id"
                :title="p.name"
                :subtitle="formatCurrency(p.total_value)"
                @click="$router.push(`/portfolios/${p.id}`)"
                class="rounded-lg mb-1"
                color="primary"
              >
                <template v-slot:append>
                  <v-chip
                    :color="Number(p.total_pnl) >= 0 ? 'success' : 'error'"
                    size="small"
                    variant="flat"
                  >
                    {{ Number(p.total_pnl) >= 0 ? '+' : '' }}{{ formatCurrency(p.total_pnl) }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>
            <div v-else class="text-medium-emphasis text-center py-4">
              {{ $t('common.no_data') }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create Portfolio Dialog -->
    <CreatePortfolioDialog v-model="showCreateDialog" @created="onPortfolioCreated" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { usePortfolioStore } from '@/stores/portfolioStore'
import CreatePortfolioDialog from '@/components/portfolio/CreatePortfolioDialog.vue'

const auth = useAuthStore()
const portfolioStore = usePortfolioStore()

const showCreateDialog = ref(false)

const portfolios = computed(() => portfolioStore.portfolios)
const summary = computed(() => portfolioStore.summary)

const pnlColor = computed(() => {
  const val = Number(summary.value?.total_pnl || 0)
  return val >= 0 ? 'success--text' : 'error--text'
})

function formatCurrency(val) {
  const num = Number(val || 0)
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(num)
}

function onPortfolioCreated() {
  portfolioStore.fetchPortfolios()
  portfolioStore.fetchSummary()
}

onMounted(() => {
  portfolioStore.fetchPortfolios()
  portfolioStore.fetchSummary()
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
