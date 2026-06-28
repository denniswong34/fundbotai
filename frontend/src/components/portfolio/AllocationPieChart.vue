<template>
  <div ref="chartRef" style="width: 100%; height: 300px"></div>
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
  const pieData = props.data.map((d) => ({
    name: d.symbol,
    value: Number(d.current_weight_pct),
    itemStyle: { color: d.color },
  }))

  chart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}% ({d}%)',
      backgroundColor: 'rgba(30, 30, 30, 0.9)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#fff' },
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '75%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        label: {
          show: true,
          formatter: '{b}\n{d}%',
          color: 'rgba(255,255,255,0.85)',
          fontSize: 11,
        },
        labelLine: {
          lineStyle: { color: 'rgba(255,255,255,0.2)' },
        },
        data: pieData.length > 0 ? pieData : [{ name: 'No Data', value: 100, itemStyle: { color: '#333' } }],
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
