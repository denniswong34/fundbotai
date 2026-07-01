<template>
  <v-card class="glass-card" elevation="0">
    <v-table density="compact" class="leaderboard-table">
      <thead>
        <tr>
          <th class="text-center" style="width:60px">#</th>
          <th class="text-left">{{ $t('arena.manager_name') }}</th>
          <th class="text-left">{{ $t('arena.model') }}</th>
          <th class="text-right">{{ $t('arena.return') }}</th>
          <th class="text-right">Alpha</th>
          <th class="text-right">Sharpe</th>
          <th class="text-center">{{ $t('arena.trades') }}</th>
          <th class="text-center">{{ $t('arena.decisions') }}</th>
          <th class="text-center" style="width:120px">{{ $t('common.actions') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="entry in entries"
          :key="entry.id"
          class="leaderboard-row"
          :class="{ 'row-top': entry.rank <= 3 }"
        >
          <td class="text-center">
            <span class="text-h6">{{ entry.medal }}</span>
          </td>
          <td>
            <div class="font-weight-bold">{{ entry.name }}</div>
            <div class="text-caption text-medium-emphasis" v-if="entry.portfolio_id">
              Portfolio #{{ entry.portfolio_id }}
            </div>
          </td>
          <td>
            <v-chip size="x-small" variant="flat" color="info">
              {{ entry.model_name }}
            </v-chip>
          </td>
          <td class="text-right">
            <span :class="entry.total_return_pct >= 0 ? 'text-success' : 'text-error'"
                  class="font-weight-bold">
              {{ entry.total_return_pct >= 0 ? '+' : '' }}{{ entry.total_return_pct.toFixed(2) }}%
            </span>
          </td>
          <td class="text-right">
            <span :class="entry.alpha_pct >= 0 ? 'text-success' : 'text-error'">
              {{ entry.alpha_pct >= 0 ? '+' : '' }}{{ entry.alpha_pct.toFixed(2) }}%
            </span>
          </td>
          <td class="text-right">{{ entry.sharpe_ratio.toFixed(2) }}</td>
          <td class="text-center">{{ entry.total_trades }}</td>
          <td class="text-center">{{ entry.decisions_count }}</td>
          <td class="text-center">
            <div class="d-flex ga-1 justify-center">
              <v-btn
                size="x-small"
                color="primary"
                variant="outlined"
                :loading="triggeringId === entry.id"
                @click="$emit('trigger', entry.id)"
              >
                {{ $t('arena.run') }}
              </v-btn>
              <v-btn
                size="x-small"
                variant="text"
                icon="mdi-chart-timeline-variant"
                @click="$emit('view-logs', entry.id)"
              />
            </div>
          </td>
        </tr>
      </tbody>
    </v-table>
    <div v-if="entries.length === 0" class="text-center pa-6 text-medium-emphasis">
      {{ $t('arena.no_managers') }}
    </div>
  </v-card>
</template>

<script setup>
defineProps({
  entries: { type: Array, default: () => [] },
  triggeringId: { type: Number, default: null },
})

defineEmits(['trigger', 'view-logs'])
</script>

<style scoped>
.leaderboard-table {
  width: 100%;
}
.leaderboard-row:hover td {
  background: rgba(255,255,255,0.02);
}
.row-top td {
  background: rgba(76, 175, 80, 0.03);
}
</style>
