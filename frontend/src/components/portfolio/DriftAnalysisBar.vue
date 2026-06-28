<template>
  <div class="drift-section mb-4">
    <div class="text-caption text-medium-emphasis mb-2">{{ $t('portfolio.drift_analysis') }}</div>
    <div v-for="h in holdings" :key="h.id" class="drift-row mb-2">
      <div class="d-flex align-center mb-1">
        <span class="text-body-2 font-weight-bold" style="min-width: 70px">{{ h.symbol }}</span>
        <span class="text-caption text-medium-emphasis ml-2">
          {{ $t('portfolio.target') }}: {{ Number(h.target_weight_pct).toFixed(2) }}%
        </span>
        <span class="text-caption text-medium-emphasis ml-2">
          {{ $t('portfolio.current') }}: {{ Number(h.current_weight_pct || 0).toFixed(2) }}%
        </span>
        <v-spacer />
        <v-chip
          :color="driftColor(h)"
          size="x-small"
          variant="flat"
        >
          {{ driftText(h) }}
        </v-chip>
      </div>
      <div class="drift-bar-bg">
        <div
          class="drift-bar-fill"
          :style="{ width: driftWidth(h), background: driftColor(h) }"
        />
        <div
          class="drift-target-marker"
          :style="{ left: targetPercent(h) }"
        />
      </div>
    </div>
    <div v-if="holdings.length === 0" class="text-center text-medium-emphasis py-2">
      {{ $t('common.no_data') }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  holdings: { type: Array, default: () => [] },
})

function driftColor(h) {
  const drift = Math.abs(Number(h.drift_pct || 0))
  if (drift <= 2) return '#4CAF50'
  if (drift <= 5) return '#FB8C00'
  return '#CF6679'
}

function driftText(h) {
  const drift = Number(h.drift_pct || 0)
  return `${drift >= 0 ? '+' : ''}${drift.toFixed(2)}%`
}

function driftWidth(h) {
  const cw = Math.max(0, Math.min(100, Number(h.current_weight_pct || 0)))
  return `${Math.max(cw, 2)}%`
}

function targetPercent(h) {
  return `${Math.max(0, Math.min(100, Number(h.target_weight_pct || 0)))}%`
}
</script>

<style scoped>
.drift-bar-bg {
  position: relative;
  height: 8px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  overflow: visible;
}
.drift-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
  min-width: 4px;
}
.drift-target-marker {
  position: absolute;
  top: -2px;
  width: 2px;
  height: 12px;
  background: rgba(255, 255, 255, 0.5);
  transition: left 0.3s;
}
</style>
