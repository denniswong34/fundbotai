<template>
  <div ref="chartRef" style="width: 100%; height: 350px"></div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let chart = null

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  if (!chart) return
  const dates = props.data.map((d) => d.date)
  const values = props.data.map((d) => Number(d.total_value))
  const pnl = props.data.map((d) => Number(d.total_pnl))

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(30, 30, 30, 0.9)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#fff' },
    },
    legend: {
      data: ['Portfolio Value', 'Total P&L'],
      textStyle: { color: 'rgba(255,255,255,0.7)' },
    },
    grid: {
      top: 40,
      left: 60,
      right: 20,
      bottom: 40,
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisLabel: { color: 'rgba(255,255,255,0.5)' },
    },
    yAxis: [
      {
        type: 'value',
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: 'rgba(255,255,255,0.5)' },
      },
      {
        type: 'value',
        splitLine: { show: false },
        axisLabel: { color: 'rgba(255,255,255,0.5)' },
      },
    ],
    series: [
      {
        name: 'Portfolio Value',
        type: 'line',
        data: values,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#4CAF50', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(76, 175, 80, 0.3)' },
            { offset: 1, color: 'rgba(76, 175, 80, 0.01)' },
          ]),
        },
      },
      {
        name: 'Total P&L',
        type: 'line',
        yAxisIndex: 1,
        data: pnl,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#2196F3', width: 2, type: 'dashed' },
      },
    ],
  })
}

watch(
  () => props.data,
  () => {
    nextTick(updateChart)
  },
  { deep: true },
)

onMounted(() => {
  nextTick(initChart)
  window.addEventListener('resize', () => chart?.resize())
})

onBeforeUnmount(() => {
  chart?.dispose()
})
</script>
