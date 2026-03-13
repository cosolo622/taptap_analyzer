<template>
  <div class="wordcloud-analysis">
    <!-- 视图切换 -->
    <el-card shadow="hover" class="view-tabs-card">
      <el-radio-group v-model="activeView" size="large">
        <el-radio-button label="wordcloud">词云视图</el-radio-button>
        <el-radio-button label="trend">趋势视图</el-radio-button>
        <el-radio-button label="heatmap">热力图视图</el-radio-button>
        <el-radio-button label="compare">对比视图</el-radio-button>
      </el-radio-group>
    </el-card>

    <!-- 词云视图 -->
    <div v-show="activeView === 'wordcloud'" class="view-content">
      <el-row :gutter="20">
        <el-col :span="16">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span>词云图</span>
                <el-select v-model="selectedWeek" placeholder="选择周" style="width: 200px;" @change="loadWordCloud">
                  <el-option v-for="week in weeks" :key="week" :label="week" :value="week" />
                </el-select>
              </div>
            </template>
            <div v-if="wordcloudUrl" style="text-align: center;">
              <img :src="wordcloudUrl" style="max-width: 100%; max-height: 500px;" />
            </div>
            <el-empty v-else description="暂无词云数据" />
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>
              <span>高频词TOP20</span>
            </template>
            <el-table :data="topWords" stripe style="width: 100%" max-height="500">
              <el-table-column type="index" label="排名" width="60" />
              <el-table-column prop="词语" label="词语" />
              <el-table-column prop="频次" label="频次" width="80" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 趋势视图 -->
    <div v-show="activeView === 'trend'" class="view-content">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>词语趋势追踪</span>
            <div class="header-controls">
              <el-dropdown trigger="click" @command="handleTrendDateCommand">
                <el-button size="small">
                  <el-icon><Calendar /></el-icon>
                  {{ trendDateLabel }}
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="all">全部周期</el-dropdown-item>
                    <el-dropdown-item command="recent4">最近4周</el-dropdown-item>
                    <el-dropdown-item command="recent8">最近8周</el-dropdown-item>
                    <el-dropdown-item command="recent12">最近12周</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-select 
                v-model="trackedWords" 
                multiple 
                filterable 
                allow-create 
                default-first-option
                placeholder="输入或选择词语追踪趋势" 
                style="width: 350px; margin-left: 10px;"
              >
                <el-option v-for="word in suggestedWords" :key="word" :label="word" :value="word" />
              </el-select>
              <el-button type="primary" @click="updateTrendChart" style="margin-left: 10px;">更新图表</el-button>
            </div>
          </div>
        </template>
        <div ref="trendChartRef" style="height: 400px;"></div>
      </el-card>
      
      <el-card shadow="hover" style="margin-top: 20px;">
        <template #header>
          <span>词语趋势数据</span>
        </template>
        <el-table :data="trendTableData" stripe style="width: 100%" max-height="300">
          <el-table-column prop="word" label="词语" width="150" fixed />
          <el-table-column v-for="week in trendWeeks" :key="week" :label="week" width="100">
            <template #default="{ row }">
              {{ row[week] || 0 }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 热力图视图 -->
    <div v-show="activeView === 'heatmap'" class="view-content">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>词语热力图（词语×周）</span>
            <div class="header-controls">
              <span class="filter-label">显示词语数：</span>
              <el-select v-model="heatmapWordCount" style="width: 100px;" @change="updateHeatmapChart">
                <el-option :value="10" label="TOP10" />
                <el-option :value="20" label="TOP20" />
                <el-option :value="30" label="TOP30" />
              </el-select>
            </div>
          </div>
        </template>
        <div ref="heatmapChartRef" style="height: 600px;"></div>
      </el-card>
    </div>

    <!-- 对比视图 -->
    <div v-show="activeView === 'compare'" class="view-content">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>双周词云对比</span>
            <div class="header-controls">
              <el-select v-model="compareWeekA" placeholder="选择周A" style="width: 180px;">
                <el-option v-for="week in weeks" :key="week" :label="week" :value="week" />
              </el-select>
              <span style="margin: 0 10px;">对比</span>
              <el-select v-model="compareWeekB" placeholder="选择周B" style="width: 180px;">
                <el-option v-for="week in weeks" :key="week" :label="week" :value="week" />
              </el-select>
              <el-button type="primary" @click="doCompare" style="margin-left: 10px;">开始对比</el-button>
            </div>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <div style="text-align: center; font-weight: bold; margin-bottom: 10px;">{{ compareWeekA }}</div>
            <div v-if="compareUrlA" style="text-align: center;">
              <img :src="compareUrlA" style="max-width: 100%; max-height: 350px;" />
            </div>
            <el-empty v-else description="请选择周A" :image-size="100" />
          </el-col>
          <el-col :span="12">
            <div style="text-align: center; font-weight: bold; margin-bottom: 10px;">{{ compareWeekB }}</div>
            <div v-if="compareUrlB" style="text-align: center;">
              <img :src="compareUrlB" style="max-width: 100%; max-height: 350px;" />
            </div>
            <el-empty v-else description="请选择周B" :image-size="100" />
          </el-col>
        </el-row>
      </el-card>

      <el-card shadow="hover" style="margin-top: 20px;">
        <template #header>
          <span>词频变化分析</span>
        </template>
        <el-table :data="compareTableData" stripe style="width: 100%" max-height="400">
          <el-table-column prop="word" label="词语" width="150" fixed />
          <el-table-column :label="compareWeekA || '周A'" width="100">
            <template #default="{ row }">{{ row.countA }}</template>
          </el-table-column>
          <el-table-column :label="compareWeekB || '周B'" width="100">
            <template #default="{ row }">{{ row.countB }}</template>
          </el-table-column>
          <el-table-column label="变化" width="120">
            <template #default="{ row }">
              <span :class="getChangeClass(row.change)">
                {{ formatChange(row.change) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row)" size="small">
                {{ getStatusText(row) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Calendar, ArrowDown } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const props = defineProps(['data'])

const activeView = ref('wordcloud')
const weeks = ref([])
const selectedWeek = ref('')
const wordcloudUrl = ref('')
const topWords = computed(() => props.data?.topWords || [])

const trackedWords = ref([])
const suggestedWords = ref([])
const trendChartRef = ref(null)
const trendWeeks = ref([])
const trendTableData = ref([])
let trendChartInstance = null

const trendDateType = ref('all')
const trendDateLabels = {
  all: '全部周期',
  recent4: '最近4周',
  recent8: '最近8周',
  recent12: '最近12周'
}
const trendDateLabel = computed(() => trendDateLabels[trendDateType.value] || '全部周期')

const handleTrendDateCommand = (cmd) => {
  trendDateType.value = cmd
  if (trackedWords.value.length > 0) {
    updateTrendChart()
  }
}

const heatmapWordCount = ref(20)
const heatmapChartRef = ref(null)
let heatmapInstance = null

const compareWeekA = ref('')
const compareWeekB = ref('')
const compareUrlA = ref('')
const compareUrlB = ref('')
const compareTableData = ref([])

const loadWordCloud = () => {
  if (selectedWeek.value) {
    wordcloudUrl.value = `/output/charts/词云_${selectedWeek.value}.png`
  }
}

const updateTrendChart = () => {
  if (!trendChartRef.value || trackedWords.value.length === 0) return
  
  const mockData = generateMockTrendData()
  trendWeeks.value = mockData.weeks
  
  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChartRef.value)
  }
  
  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#48b8d0']
  const series = trackedWords.value.map((word, idx) => ({
    name: word,
    type: 'line',
    smooth: true,
    data: mockData.data[word] || [],
    itemStyle: { color: colors[idx % colors.length] },
    label: {
      show: true,
      position: 'top',
      fontSize: 10,
      color: colors[idx % colors.length],
      formatter: '{c}'
    }
  }))
  
  trendChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { bottom: '5%', type: 'scroll' },
    xAxis: { type: 'category', data: mockData.weeks, axisLabel: { rotate: 45 } },
    yAxis: { type: 'value' },
    series,
    grid: { bottom: 100, right: 30, left: 50, top: 40 }
  })
  
  trendTableData.value = trackedWords.value.map(word => {
    const row = { word }
    mockData.weeks.forEach((week, idx) => {
      row[week] = mockData.data[word]?.[idx] || 0
    })
    return row
  })
}

/**
 * 根据日期筛选类型获取周数
 */
const getWeeksByDateType = () => {
  const weeksList = props.data?.weeks || []
  switch (trendDateType.value) {
    case 'recent4':
      return weeksList.slice(-4)
    case 'recent8':
      return weeksList.slice(-8)
    case 'recent12':
      return weeksList.slice(-12)
    default:
      return weeksList.slice(-20)
  }
}

const generateMockTrendData = () => {
  const weeksList = getWeeksByDateType()
  const result = { weeks: weeksList, data: {} }
  
  trackedWords.value.forEach(word => {
    result.data[word] = weeksList.map(() => Math.floor(Math.random() * 50) + 5)
  })
  
  return result
}

const updateHeatmapChart = () => {
  if (!heatmapChartRef.value || !props.data?.weeks) return
  
  const weeksList = props.data.weeks.slice(-15)
  const words = topWords.value.slice(0, heatmapWordCount.value).map(w => w['词语'])
  
  const data = []
  words.forEach((word, wordIdx) => {
    weeksList.forEach((week, weekIdx) => {
      data.push([weekIdx, wordIdx, Math.floor(Math.random() * 50) + 5])
    })
  })
  
  if (!heatmapInstance) {
    heatmapInstance = echarts.init(heatmapChartRef.value)
  }
  
  heatmapInstance.setOption({
    tooltip: {
      position: 'top',
      formatter: (params) => `${weeksList[params.data[0]]} - ${words[params.data[1]]}: ${params.data[2]}次`
    },
    xAxis: { 
      type: 'category', 
      data: weeksList, 
      axisLabel: { rotate: 45 },
      splitArea: { show: true }
    },
    yAxis: { 
      type: 'category', 
      data: words,
      splitArea: { show: true }
    },
    visualMap: {
      min: 0,
      max: 50,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%',
      inRange: {
        color: ['#f5f5f5', '#c6e48b', '#7bc96f', '#239a3b', '#196127']
      }
    },
    series: [{
      type: 'heatmap',
      data: data,
      label: { show: false },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' }
      }
    }],
    grid: { left: 100, right: 30, top: 20, bottom: 120 }
  })
}

const doCompare = () => {
  if (compareWeekA.value) {
    compareUrlA.value = `/output/charts/词云_${compareWeekA.value}.png`
  }
  if (compareWeekB.value) {
    compareUrlB.value = `/output/charts/词云_${compareWeekB.value}.png`
  }
  
  generateCompareTable()
}

const generateCompareTable = () => {
  const mockWords = ['外挂', '卡顿', '闪退', '新角色', '平衡性', '匹配', '网络', '骂人', '新手', '活动']
  compareTableData.value = mockWords.map(word => {
    const countA = Math.floor(Math.random() * 50)
    const countB = Math.floor(Math.random() * 50)
    const change = countA > 0 ? ((countB - countA) / countA * 100) : (countB > 0 ? 100 : 0)
    return { word, countA, countB, change }
  }).sort((a, b) => Math.abs(b.change) - Math.abs(a.change))
}

const getChangeClass = (change) => {
  if (change > 50) return 'change-up-high'
  if (change > 0) return 'change-up'
  if (change < -50) return 'change-down-high'
  if (change < 0) return 'change-down'
  return ''
}

const formatChange = (change) => {
  if (change > 0) return `↑${change.toFixed(1)}%`
  if (change < 0) return `↓${Math.abs(change).toFixed(1)}%`
  return '持平'
}

const getStatusType = (row) => {
  if (row.countA === 0 && row.countB > 0) return 'danger'
  if (row.countA > 0 && row.countB === 0) return 'info'
  if (row.change > 50) return 'warning'
  if (row.change < -50) return 'success'
  return ''
}

const getStatusText = (row) => {
  if (row.countA === 0 && row.countB > 0) return '新增热点'
  if (row.countA > 0 && row.countB === 0) return '消失词'
  if (row.change > 50) return '快速上升'
  if (row.change < -50) return '快速下降'
  return '正常波动'
}

watch(() => props.data, () => {
  if (props.data?.weeks) {
    weeks.value = props.data.weeks
    if (weeks.value.length > 0) {
      selectedWeek.value = weeks.value[weeks.value.length - 1]
      compareWeekA.value = weeks.value[weeks.value.length - 2] || weeks.value[0]
      compareWeekB.value = weeks.value[weeks.value.length - 1]
      loadWordCloud()
    }
  }
  if (props.data?.topWords) {
    suggestedWords.value = props.data.topWords.slice(0, 30).map(w => w['词语'])
  }
}, { deep: true })

watch(activeView, (newView) => {
  nextTick(() => {
    if (newView === 'trend' && trackedWords.value.length > 0) {
      updateTrendChart()
    } else if (newView === 'heatmap') {
      updateHeatmapChart()
    }
  })
})

onMounted(() => {
  if (props.data?.weeks) {
    weeks.value = props.data.weeks
    if (weeks.value.length > 0) {
      selectedWeek.value = weeks.value[weeks.value.length - 1]
      compareWeekA.value = weeks.value[weeks.value.length - 2] || weeks.value[0]
      compareWeekB.value = weeks.value[weeks.value.length - 1]
      loadWordCloud()
    }
  }
  if (props.data?.topWords) {
    suggestedWords.value = props.data.topWords.slice(0, 30).map(w => w['词语'])
  }
})
</script>

<style scoped>
.wordcloud-analysis {
  padding: 0;
}

.view-tabs-card {
  margin-bottom: 20px;
}

.view-content {
  margin-top: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  align-items: center;
}

.filter-label {
  font-weight: 500;
  color: #606266;
  margin-right: 10px;
}

.change-up {
  color: #e6a23c;
}

.change-up-high {
  color: #f56c6c;
  font-weight: bold;
}

.change-down {
  color: #67c23a;
}

.change-down-high {
  color: #67c23a;
  font-weight: bold;
}
</style>
