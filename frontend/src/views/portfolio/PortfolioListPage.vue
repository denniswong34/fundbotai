<template>
  <div>
    <v-row>
      <v-col cols="12" class="d-flex align-center justify-space-between">
        <h2 class="text-h4 font-weight-bold">{{ $t('portfolio.title') }}</h2>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="showCreateDialog = true">
          {{ $t('portfolio.create') }}
        </v-btn>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col v-if="loading" cols="12" class="text-center py-8">
        <v-progress-circular indeterminate color="primary" />
      </v-col>

      <v-col v-else-if="portfolios.length === 0" cols="12" class="text-center py-8">
        <v-icon size="64" color="text-disabled" class="mb-4">mdi-briefcase-variant-off</v-icon>
        <div class="text-h6 text-medium-emphasis">{{ $t('common.no_data') }}</div>
      </v-col>

      <v-col v-for="p in portfolios" :key="p.id" cols="12" md="6" lg="4">
        <v-card class="glass-card" elevation="0" @click="$router.push(`/portfolios/${p.id}`)" style="cursor: pointer">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" color="primary">mdi-briefcase-variant</v-icon>
            <span class="font-weight-bold">{{ p.name }}</span>
            <v-spacer />
            <v-btn icon variant="text" size="small" @click.stop="confirmDelete(p)">
              <v-icon color="error">mdi-delete</v-icon>
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis">{{ $t('portfolio.total_value') }}</div>
                <div class="text-h6 font-weight-bold">{{ formatCurrency(p.total_value) }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis">{{ $t('portfolio.total_pnl') }}</div>
                <div class="text-h6 font-weight-bold" :class="Number(p.total_pnl) >= 0 ? 'text-success' : 'text-error'">
                  {{ Number(p.total_pnl) >= 0 ? '+' : '' }}{{ formatCurrency(p.total_pnl) }}
                  <span class="text-body-2">({{ Number(p.total_pnl_pct).toFixed(2) }}%)</span>
                </div>
              </v-col>
            </v-row>
            <v-row class="mt-2">
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis">{{ $t('common.currency') }}</div>
                <div>{{ p.base_currency }}</div>
              </v-col>
              <v-col cols="6" v-if="p.last_rebalanced_at">
                <div class="text-caption text-medium-emphasis">{{ $t('common.last_rebalanced') }}</div>
                <div class="text-body-2">{{ formatDate(p.last_rebalanced_at) }}</div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <CreatePortfolioDialog v-model="showCreateDialog" @created="onCreated" />

    <!-- Delete Confirm Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card class="glass-card">
        <v-card-title>{{ $t('portfolio.delete') }}</v-card-title>
        <v-card-text>
          {{ $t('common.confirm_delete') }} "{{ deletingPortfolio?.name }}"?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" @click="doDelete">{{ $t('common.delete') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePortfolioStore } from '@/stores/portfolioStore'
import { useRouter } from 'vue-router'
import CreatePortfolioDialog from '@/components/portfolio/CreatePortfolioDialog.vue'

const portfolioStore = usePortfolioStore()
const router = useRouter()

const showCreateDialog = ref(false)
const deleteDialog = ref(false)
const deletingPortfolio = ref(null)

const portfolios = computed(() => portfolioStore.portfolios)
const loading = computed(() => portfolioStore.loading)

function formatCurrency(val) {
  const num = Number(val || 0)
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(num)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}

function confirmDelete(p) {
  deletingPortfolio.value = p
  deleteDialog.value = true
}

async function doDelete() {
  if (!deletingPortfolio.value) return
  await portfolioStore.deletePortfolio(deletingPortfolio.value.id)
  deleteDialog.value = false
  deletingPortfolio.value = null
}

function onCreated() {
  portfolioStore.fetchPortfolios()
}

onMounted(() => {
  portfolioStore.fetchPortfolios()
})
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  transition: transform 0.2s, border-color 0.2s;
}
.glass-card:hover {
  transform: translateY(-2px);
  border-color: rgba(76, 175, 80, 0.3);
}
</style>
