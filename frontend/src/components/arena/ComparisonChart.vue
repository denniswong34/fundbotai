<template>
  <div ref="chartRef" style="width: 100%; height: 400px"></div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  series: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let chart = null

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  if (!chart || props.series.length === 0) return

  const series_data = props.series.map(s => ({
    name: s.manager_name,
    type: 'line',
    smooth: true,
    symbol: 'none',
    lineStyle: { color: s.color, width: 2 },
    data: (s.data || []).map(d => Number(d.value)),
  }))

  // Use the first series dates as x-axis
  const dates = (props.series[0]?.data || []).map(d => d.date)

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(30, 30, 30, 0.9)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#fff' },
    },
    legend: {
      data: props.series.map(s => s.manager_name),
      textStyle: { color: 'rgba(255,255,255,0.7)' },
      bottom: 0,
    },
    grid: {
      top: 20,
      left: 60,
      right: 20,
      bottom: 50,
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisLabel: { color: 'rgba(255,255,255,0.5)', rotate: 30 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      axisLabel: {
        color: 'rgba(255,255,255,0.5)',
        formatter: (v) => '$' + v.toLocaleString(),
      },
    },
    series: series_data,
  })
}

watch(
  () => props.series,
  () => nextTick(updateChart),
  { deep: true }
)

onMounted(() => {
  nextTick(initChart)
  window.addEventListener('resize', () => chart?.resize())
})

onBeforeUnmount(() => {
  chart?.dispose()
})
</script>
