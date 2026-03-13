<template>
  <div class="overview">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" style="background: #409eff;">
            <el-icon size="32"><Document /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-value">{{ data?.total || 0 }}</div>
            <div class="metric-label">总评价数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" style="background: #e6a23c;">
            <el-icon size="32"><StarFilled /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-value">{{ data?.avgRating?.toFixed(2) || 0 }}</div>
            <div class="metric-label">平均星级</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" style="background: #67c23a;">
            <el-icon size="32"><CircleCheck /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-value">{{ data?.positive || 0 }}</div>
            <div class="metric-label">正向评价</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" style="background: #f56c6c;">
            <el-icon size="32"><CircleClose /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-value">{{ data?.negative || 0 }}</div>
            <div class="metric-label">负向评价</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>情感分布</span>
          </template>
          <div ref="pieChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>评价数量趋势</span>
          </template>
          <div ref="lineChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <span>问题分类TOP10</span>
          </template>
          <div ref="barChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Document, StarFilled, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const props = defineProps(['data'])
const pieChart = ref(null)
const lineChart = ref(null)
const barChart = ref(null)

const initCharts = () => {
  if (!props.data) return

  const pieChartInstance = echarts.init(pieChart.value)
  pieChartInstance.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: '5%' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
      data: props.data.sentimentDistribution || []
    }]
  })

  const lineChartInstance = echarts.init(lineChart.value)
  lineChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: props.data.dates || [] },
    yAxis: { type: 'value' },
    series: [{
      data: props.data.dailyCounts || [],
      type: 'line',
      smooth: true,
      areaStyle: { opacity: 0.3 }
    }]
  })

  const barChartInstance = echarts.init(barChart.value)
  barChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: (props.data.topProblems || []).map(p => p.name) },
    series: [{
      type: 'bar',
      data: (props.data.topProblems || []).map(p => p.value),
      itemStyle: { borderRadius: [0, 4, 4, 0] }
    }]
  })
}

watch(() => props.data, initCharts, { deep: true })
onMounted(initCharts)
</script>

<style scoped>
.metric-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.metric-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.metric-info {
  margin-left: 20px;
}

.metric-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.metric-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}
</style>
