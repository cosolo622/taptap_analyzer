<template>
  <div class="negative-monitor">
    <!-- 顶部标题栏 -->
    <div class="dashboard-header">
      <div class="header-left">
        <h2 class="dashboard-title">负面舆情监控</h2>
        <span class="refresh-time">数据更新时间：{{ lastRefreshTime }}</span>
      </div>
      <div class="header-right">
        <el-dropdown trigger="click" @command="handleDateCommand">
          <el-button size="small">
            <el-icon><Calendar /></el-icon>
            {{ dateLabel }}
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="today">今日</el-dropdown-item>
              <el-dropdown-item command="week">过去7天</el-dropdown-item>
              <el-dropdown-item command="month">过去30天</el-dropdown-item>
              <el-dropdown-item command="thisMonth">本月</el-dropdown-item>
              <el-dropdown-item divided>
                <el-date-picker
                  v-model="customDateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始"
                  end-placeholder="结束"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  @change="handleCustomDateChange"
                  style="width: 240px;"
                />
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 负面舆情概览 -->
    <el-row :gutter="20" class="metrics-row">
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card negative">
          <div class="metric-icon">
            <el-icon size="32"><Warning /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-value">{{ negativeMetrics.total }}</div>
            <div class="metric-label">负面评价总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" style="background: #e6a23c;">
            <el-icon size="32"><TrendCharts /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-value">{{ negativeMetrics.rate?.toFixed(1) || 0 }}%</div>
            <div class="metric-label">负面评价占比</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" style="background: #909399;">
            <el-icon size="32"><StarFilled /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-value">{{ negativeMetrics.avgRating?.toFixed(2) || '0.00' }}</div>
            <div class="metric-label">负面评价平均星级</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" style="background: #409eff;">
            <el-icon size="32"><Timer /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-value">{{ negativeMetrics.trend }}</div>
            <div class="metric-label">环比趋势</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 负面问题TOP10 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>负面问题TOP10</span>
            </div>
          </template>
          <div ref="topProblemChart" style="height: 350px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>负面评价星级分布</span>
            </div>
          </template>
          <div ref="ratingDistChart" style="height: 350px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 负面趋势分析 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>负面评价趋势分析</span>
              <el-radio-group v-model="trendAggregation" size="small" @change="updateTrendChart">
                <el-radio-button label="day">按天</el-radio-button>
                <el-radio-button label="week">按周</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 问题分类详情 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>负面问题分类详情</span>
              <el-button type="primary" size="small" @click="exportCSV">
                <el-icon><Download /></el-icon>
                导出CSV
              </el-button>
            </div>
          </template>
          <el-table :data="problemDetailData" stripe style="width: 100%" max-height="400">
            <el-table-column prop="category" label="问题分类" width="200" />
            <el-table-column prop="count" label="出现次数" width="120" sortable />
            <el-table-column prop="rate" label="占比" width="100">
              <template #default="{ row }">
                {{ (row.rate * 100).toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column prop="avgRating" label="平均星级" width="120">
              <template #default="{ row }">
                {{ row.avgRating?.toFixed(2) || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="trend" label="环比变化" width="120">
              <template #default="{ row }">
                <span :class="row.trend > 0 ? 'trend-up' : row.trend < 0 ? 'trend-down' : ''">
                  {{ row.trend > 0 ? '↑' : row.trend < 0 ? '↓' : '' }}{{ Math.abs(row.trend || 0).toFixed(1) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="sample" label="典型评价" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 负面评价词云 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <span>负面评价高频词TOP20</span>
          </template>
          <div ref="wordFreqChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Warning, TrendCharts, StarFilled, Timer, Download, Calendar, ArrowDown } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const props = defineProps(['data'])

const STORAGE_KEY = 'negative_monitor_settings'

const lastRefreshTime = ref(new Date().toLocaleString('zh-CN'))
const dateType = ref('week')
const dateRange = ref([])
const customDateRange = ref(null)
const trendAggregation = ref('day')

const dateTypeLabels = {
  today: '今日',
  week: '过去7天',
  month: '过去30天',
  thisMonth: '本月',
  custom: '自定义'
}

const dateLabel = computed(() => dateTypeLabels[dateType.value] || '选择日期')

const topProblemChart = ref(null)
const ratingDistChart = ref(null)
const trendChart = ref(null)
const wordFreqChart = ref(null)

let topProblemInstance = null
let ratingDistInstance = null
let trendInstance = null
let wordFreqInstance = null

const getDateRangeByType = (type) => {
  const today = new Date()
  const formatDate = (d) => d.toISOString().split('T')[0]
  
  switch (type) {
    case 'today':
      return [formatDate(today), formatDate(today)]
    case 'week':
      const weekAgo = new Date(today)
      weekAgo.setDate(weekAgo.getDate() - 7)
      return [formatDate(weekAgo), formatDate(today)]
    case 'month':
      const monthAgo = new Date(today)
      monthAgo.setDate(monthAgo.getDate() - 30)
      return [formatDate(monthAgo), formatDate(today)]
    case 'thisMonth':
      const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)
      return [formatDate(firstDay), formatDate(today)]
    default:
      return []
  }
}

const handleDateCommand = (cmd) => {
  dateType.value = cmd
  dateRange.value = getDateRangeByType(cmd)
  saveSettings()
  nextTick(() => {
    updateAllCharts()
  })
}

const handleCustomDateChange = () => {
  if (customDateRange.value && customDateRange.value.length === 2) {
    dateType.value = 'custom'
    dateRange.value = customDateRange.value
    saveSettings()
    nextTick(() => {
      updateAllCharts()
    })
  }
}

const saveSettings = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    dateType: dateType.value,
    trendAggregation: trendAggregation.value
  }))
}

const loadSettings = () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    const settings = JSON.parse(saved)
    if (settings.dateType) dateType.value = settings.dateType
    if (settings.trendAggregation) trendAggregation.value = settings.trendAggregation
  }
  dateRange.value = getDateRangeByType(dateType.value)
}

const getFilteredReviews = () => {
  if (!props.data?.reviews) return []
  let reviews = props.data.reviews
  if (dateRange.value && dateRange.value.length === 2) {
    const [start, end] = dateRange.value
    reviews = reviews.filter(r => r['日期'] >= start && r['日期'] <= end)
  }
  return reviews
}

const getNegativeReviews = () => {
  const reviews = getFilteredReviews()
  return reviews.filter(r => r['情感'] === '负向' || r['情感'] === '中性偏负')
}

const negativeMetrics = computed(() => {
  const allReviews = getFilteredReviews()
  const negativeReviews = getNegativeReviews()
  const total = negativeReviews.length
  const rate = allReviews.length > 0 ? (total / allReviews.length) * 100 : 0
  const avgRating = total > 0 ? negativeReviews.reduce((sum, r) => sum + (r['星级'] || 0), 0) / total : 0
  
  const today = new Date()
  const weekAgo = new Date(today)
  weekAgo.setDate(weekAgo.getDate() - 7)
  const twoWeekAgo = new Date(today)
  twoWeekAgo.setDate(twoWeekAgo.getDate() - 14)
  
  const formatDate = (d) => d.toISOString().split('T')[0]
  const thisWeekNeg = allReviews.filter(r => 
    r['日期'] >= formatDate(weekAgo) && r['日期'] <= formatDate(today) && 
    (r['情感'] === '负向' || r['情感'] === '中性偏负')
  ).length
  const lastWeekNeg = allReviews.filter(r => 
    r['日期'] >= formatDate(twoWeekAgo) && r['日期'] < formatDate(weekAgo) && 
    (r['情感'] === '负向' || r['情感'] === '中性偏负')
  ).length
  
  const trendValue = lastWeekNeg > 0 ? ((thisWeekNeg - lastWeekNeg) / lastWeekNeg * 100) : 0
  const trend = trendValue > 0 ? `↑${trendValue.toFixed(1)}%` : trendValue < 0 ? `↓${Math.abs(trendValue).toFixed(1)}%` : '持平'
  
  return { total, rate, avgRating, trend }
})

const problemDetailData = computed(() => {
  const negativeReviews = getNegativeReviews()
  const problemCount = {}
  const problemRatings = {}
  const problemSamples = {}
  
  negativeReviews.forEach(r => {
    const problem = r['问题分类'] || '未分类'
    problemCount[problem] = (problemCount[problem] || 0) + 1
    if (!problemRatings[problem]) problemRatings[problem] = []
    problemRatings[problem].push(r['星级'] || 0)
    if (!problemSamples[problem] && r['一句话摘要']) {
      problemSamples[problem] = r['一句话摘要']
    }
  })
  
  const total = negativeReviews.length
  return Object.entries(problemCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20)
    .map(([category, count]) => ({
      category,
      count,
      rate: total > 0 ? count / total : 0,
      avgRating: problemRatings[category]?.length > 0 
        ? problemRatings[category].reduce((a, b) => a + b, 0) / problemRatings[category].length 
        : 0,
      trend: 0,
      sample: problemSamples[category] || '-'
    }))
})

const updateTopProblemChart = () => {
  if (!topProblemChart.value) return
  
  const negativeReviews = getNegativeReviews()
  const problemCount = {}
  negativeReviews.forEach(r => {
    const problem = r['问题分类']?.split('-')[0]?.trim() || '未分类'
    if (problem && problem !== '无问题') {
      problemCount[problem] = (problemCount[problem] || 0) + 1
    }
  })
  
  const sorted = Object.entries(problemCount).sort((a, b) => b[1] - a[1]).slice(0, 10)
  
  if (!topProblemInstance) {
    topProblemInstance = echarts.init(topProblemChart.value)
  }
  
  topProblemInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: sorted.map(s => s[0]).reverse() },
    series: [{
      type: 'bar',
      data: sorted.map(s => s[1]).reverse(),
      itemStyle: { borderRadius: [0, 4, 4, 0], color: '#f56c6c' }
    }],
    grid: { left: 100, right: 30, top: 20, bottom: 20 }
  })
}

const updateRatingDistChart = () => {
  if (!ratingDistChart.value) return
  
  const negativeReviews = getNegativeReviews()
  const ratingCount = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
  negativeReviews.forEach(r => {
    const rating = r['星级']
    if (rating >= 1 && rating <= 5) {
      ratingCount[rating]++
    }
  })
  
  if (!ratingDistInstance) {
    ratingDistInstance = echarts.init(ratingDistChart.value)
  }
  
  ratingDistInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}星: {c}条 ({d}%)' },
    legend: { bottom: '5%' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: Object.entries(ratingCount)
        .filter(([_, v]) => v > 0)
        .map(([k, v]) => ({ name: `${k}星`, value: v })),
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}: {c}' },
      color: ['#f56c6c', '#e6a23c', '#909399', '#67c23a', '#409eff']
    }]
  })
}

const updateTrendChart = () => {
  if (!trendChart.value) return
  
  const allReviews = getFilteredReviews()
  const groups = {}
  
  allReviews.forEach(r => {
    let key = r['日期']
    if (trendAggregation.value === 'week') {
      const d = new Date(r['日期'])
      const weekStart = new Date(d)
      weekStart.setDate(d.getDate() - d.getDay())
      key = weekStart.toISOString().split('T')[0]
    }
    if (!groups[key]) groups[key] = []
    groups[key].push(r)
  })
  
  const periods = Object.keys(groups).sort()
  const negativeCounts = periods.map(p => 
    groups[p].filter(r => r['情感'] === '负向' || r['情感'] === '中性偏负').length
  )
  const totalCounts = periods.map(p => groups[p].length)
  const negativeRates = periods.map((p, i) => 
    totalCounts[i] > 0 ? (negativeCounts[i] / totalCounts[i] * 100).toFixed(1) : 0
  )
  
  if (!trendInstance) {
    trendInstance = echarts.init(trendChart.value)
  }
  
  trendInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['负面评价数', '负面占比'], bottom: '5%' },
    xAxis: { type: 'category', data: periods, axisLabel: { rotate: 45 } },
    yAxis: [
      { type: 'value', name: '数量' },
      { type: 'value', name: '占比(%)', max: 100 }
    ],
    series: [
      {
        name: '负面评价数',
        type: 'bar',
        data: negativeCounts,
        itemStyle: { color: '#f56c6c' }
      },
      {
        name: '负面占比',
        type: 'line',
        yAxisIndex: 1,
        data: negativeRates,
        itemStyle: { color: '#e6a23c' },
        smooth: true
      }
    ],
    grid: { left: 60, right: 60, bottom: 80, top: 40 }
  })
}

const updateWordFreqChart = () => {
  if (!wordFreqChart.value) return
  
  const negativeReviews = getNegativeReviews()
  const wordCount = {}
  
  negativeReviews.forEach(r => {
    const summary = r['一句话摘要'] || ''
    const words = summary.split(/[，。！？、\s]+/).filter(w => w.length >= 2)
    words.forEach(w => {
      wordCount[w] = (wordCount[w] || 0) + 1
    })
  })
  
  const sorted = Object.entries(wordCount).sort((a, b) => b[1] - a[1]).slice(0, 20)
  
  if (!wordFreqInstance) {
    wordFreqInstance = echarts.init(wordFreqChart.value)
  }
  
  wordFreqInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'category', data: sorted.map(s => s[0]), axisLabel: { rotate: 45 } },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      data: sorted.map(s => s[1]),
      itemStyle: { color: '#909399', borderRadius: [4, 4, 0, 0] }
    }],
    grid: { left: 50, right: 30, bottom: 80, top: 20 }
  })
}

const exportCSV = () => {
  if (problemDetailData.value.length === 0) return
  
  const headers = ['问题分类', '出现次数', '占比', '平均星级', '环比变化', '典型评价']
  const rows = problemDetailData.value.map(row => [
    row.category,
    row.count,
    (row.rate * 100).toFixed(1) + '%',
    row.avgRating?.toFixed(2) || '',
    row.trend?.toFixed(1) + '%' || '0%',
    row.sample
  ])
  
  const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
  const BOM = '\uFEFF'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `负面舆情分析_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

const updateAllCharts = () => {
  updateTopProblemChart()
  updateRatingDistChart()
  updateTrendChart()
  updateWordFreqChart()
}

watch(() => props.data, () => {
  if (props.data) {
    nextTick(() => {
      updateAllCharts()
    })
  }
}, { deep: true })

onMounted(() => {
  loadSettings()
  if (props.data) {
    nextTick(() => {
      updateAllCharts()
    })
  }
})
</script>

<style scoped>
.negative-monitor {
  padding: 0;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  margin-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 15px;
}

.dashboard-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.refresh-time {
  font-size: 12px;
  color: #909399;
}

.header-right {
  display: flex;
  gap: 10px;
}

.metrics-row {
  margin-bottom: 0;
}

.metric-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.metric-card.negative {
  border-left: 4px solid #f56c6c;
}

.metric-card.negative .metric-icon {
  background: #f56c6c;
}

.metric-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  background: #f56c6c;
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.trend-up {
  color: #f56c6c;
  font-weight: bold;
}

.trend-down {
  color: #67c23a;
  font-weight: bold;
}
</style>
