<template>
  <div class="sentiment">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>情感分布饼图</span>
          </template>
          <div ref="pieChart" style="height: 400px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>情感分布条形图</span>
          </template>
          <div ref="barChart" style="height: 400px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>情感分天趋势</span>
              <el-radio-group v-model="chartType" size="small">
                <el-radio-button label="line">折线图</el-radio-button>
                <el-radio-button label="bar">柱状图</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChart" style="height: 400px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <span>情感分周统计</span>
          </template>
          <el-table :data="data?.weeklyData || []" stripe style="width: 100%">
            <el-table-column prop="周标签" label="周" width="150" />
            <el-table-column prop="正向" label="正向" width="100" />
            <el-table-column prop="负向" label="负向" width="100" />
            <el-table-column prop="中性" label="中性" width="100" />
            <el-table-column prop="中性偏负" label="中性偏负" width="100" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps(['data'])
const chartType = ref('line')
const pieChart = ref(null)
const barChart = ref(null)
const trendChart = ref(null)

const initCharts = () => {
  if (!props.data) return

  const pieChartInstance = echarts.init(pieChart.value)
  pieChartInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: '5%' },
    color: ['#67C23A', '#E6A23C', '#F56C6C', '#909399'],
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}: {d}%' },
      data: props.data.sentimentDistribution || []
    }]
  })

  const barChartInstance = echarts.init(barChart.value)
  barChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: (props.data.sentimentDistribution || []).map(s => s.name) },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      data: (props.data.sentimentDistribution || []).map(s => s.value),
      itemStyle: {
        color: (params) => ['#67C23A', '#E6A23C', '#F56C6C', '#909399'][params.dataIndex]
      }
    }]
  })

  initTrendChart()
}

const initTrendChart = () => {
  const trendChartInstance = echarts.init(trendChart.value)
  const series = (props.data?.sentimentTrend || []).map(item => ({
    name: item.name,
    type: chartType.value,
    data: item.data,
    smooth: chartType.value === 'line'
  }))

  trendChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: (props.data?.sentimentTrend || []).map(s => s.name) },
    xAxis: { type: 'category', data: props.data?.dates || [] },
    yAxis: { type: 'value' },
    series
  })
}

watch(() => props.data, initCharts, { deep: true })
watch(chartType, initTrendChart)
onMounted(initCharts)
</script>

<style scoped>
.sentiment {
  padding: 0;
}
</style>
