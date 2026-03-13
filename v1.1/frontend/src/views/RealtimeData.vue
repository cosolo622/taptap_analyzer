<template>
  <div class="realtime-data">
    <!-- 顶部标题栏 -->
    <div class="dashboard-header">
      <div class="header-left">
        <h2 class="dashboard-title">实时舆情监控看板</h2>
        <span class="refresh-time">数据更新时间：{{ lastRefreshTime }}</span>
      </div>
      <div class="header-right">
        <el-dropdown trigger="click" @command="handleGlobalDateCommand">
          <el-button size="small">
            <el-icon><Calendar /></el-icon>
            {{ globalDateLabel }}
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
        <el-button size="small" @click="refreshData" :loading="isRefreshing">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 图表设置弹窗 -->
    <el-dialog v-model="chartSettingVisible" :title="chartSettingTitle" width="400px">
      <div class="setting-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>设置此报表的默认展示方式，保存后下次打开自动应用</span>
      </div>
      <el-form label-width="100px" style="margin-top: 20px;">
        <el-form-item label="聚合方式" v-if="currentChartSetting.hasAggregation">
          <el-select v-model="currentChartSetting.aggregation" style="width: 200px;">
            <el-option label="按天" value="day" />
            <el-option label="按周" value="week" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-select v-model="currentChartSetting.dateType" style="width: 200px;">
            <el-option label="今日" value="today" />
            <el-option label="过去7天" value="week" />
            <el-option label="过去30天" value="month" />
            <el-option label="本月" value="thisMonth" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="chartSettingVisible = false">取消</el-button>
        <el-button type="primary" @click="saveChartSetting">保存设置</el-button>
      </template>
    </el-dialog>

    <!-- 顶部指标卡 -->
    <el-row :gutter="20" class="metrics-row">
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" style="background: #409eff;">
            <el-icon size="32"><Document /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-value">{{ metrics.total }}</div>
            <div class="metric-label">评价数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" style="background: #e6a23c;">
            <el-icon size="32"><StarFilled /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-value">{{ metrics.avgRating?.toFixed(2) || '0.00' }}</div>
            <div class="metric-label">平均星级</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" style="background: #f56c6c;">
            <el-icon size="32"><CircleClose /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-value">{{ metrics.negative }}</div>
            <div class="metric-label">负面评价</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" style="background: #67c23a;">
            <el-icon size="32"><CircleCheck /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-value">{{ metrics.positive }}</div>
            <div class="metric-label">正向评价</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 评价数量趋势 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">评价数量趋势</span>
              <el-button text size="small" class="card-setting-btn" @click="openChartSetting('trend', '评价数量趋势', true)">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="chart-controls">
            <el-dropdown trigger="click" @command="(cmd) => handleAggregationChange('trend', cmd)">
              <el-button size="small">
                {{ trendAggregation === 'day' ? '按天' : '按周' }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="day">按天</el-dropdown-item>
                  <el-dropdown-item command="week">按周</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-dropdown trigger="click" @command="(cmd) => handleChartDateChange('trend', cmd)">
              <el-button size="small">
                {{ trendDateLabel }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="today">今日</el-dropdown-item>
                  <el-dropdown-item command="week">过去7天</el-dropdown-item>
                  <el-dropdown-item command="month">过去30天</el-dropdown-item>
                  <el-dropdown-item>
                    <el-date-picker
                      v-model="trendCustomDate"
                      type="daterange"
                      range-separator="-"
                      format="MM-DD"
                      value-format="YYYY-MM-DD"
                      placeholder="自定义"
                      @change="handleChartCustomDate('trend')"
                      style="width: 180px;"
                    />
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div ref="trendChart" style="height: 280px;"></div>
        </el-card>
      </el-col>
      <!-- 情感分布饼图 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">情感分布</span>
              <el-button text size="small" class="card-setting-btn" @click="openChartSetting('sentimentPie', '情感分布', false)">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="chart-controls">
            <el-dropdown trigger="click" @command="(cmd) => handleChartDateChange('sentimentPie', cmd)">
              <el-button size="small">
                {{ sentimentPieDateLabel }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="today">今日</el-dropdown-item>
                  <el-dropdown-item command="week">过去7天</el-dropdown-item>
                  <el-dropdown-item command="month">过去30天</el-dropdown-item>
                  <el-dropdown-item>
                    <el-date-picker
                      v-model="sentimentPieCustomDate"
                      type="daterange"
                      range-separator="-"
                      format="MM-DD"
                      value-format="YYYY-MM-DD"
                      placeholder="自定义"
                      @change="handleChartCustomDate('sentimentPie')"
                      style="width: 180px;"
                    />
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div ref="sentimentPieChart" style="height: 280px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 情感分天趋势 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">情感类型趋势</span>
              <el-button text size="small" class="card-setting-btn" @click="openChartSetting('sentimentTrend', '情感类型趋势', true)">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="chart-controls">
            <el-dropdown trigger="click" @command="(cmd) => handleAggregationChange('sentiment', cmd)">
              <el-button size="small">
                {{ sentimentAggregation === 'day' ? '按天' : '按周' }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="day">按天</el-dropdown-item>
                  <el-dropdown-item command="week">按周</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-dropdown trigger="click" @command="(cmd) => handleChartDateChange('sentimentTrend', cmd)">
              <el-button size="small">
                {{ sentimentTrendDateLabel }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="today">今日</el-dropdown-item>
                  <el-dropdown-item command="week">过去7天</el-dropdown-item>
                  <el-dropdown-item command="month">过去30天</el-dropdown-item>
                  <el-dropdown-item>
                    <el-date-picker
                      v-model="sentimentTrendCustomDate"
                      type="daterange"
                      range-separator="-"
                      format="MM-DD"
                      value-format="YYYY-MM-DD"
                      placeholder="自定义"
                      @change="handleChartCustomDate('sentimentTrend')"
                      style="width: 180px;"
                    />
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div ref="sentimentTrendChart" style="height: 280px;"></div>
        </el-card>
      </el-col>
      <!-- 问题大类分布 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">问题大类分布</span>
              <el-button text size="small" class="card-setting-btn" @click="openChartSetting('problemPie', '问题大类分布', false)">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="chart-controls">
            <el-dropdown trigger="click" @command="(cmd) => handleChartDateChange('problemPie', cmd)">
              <el-button size="small">
                {{ problemPieDateLabel }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="today">今日</el-dropdown-item>
                  <el-dropdown-item command="week">过去7天</el-dropdown-item>
                  <el-dropdown-item command="month">过去30天</el-dropdown-item>
                  <el-dropdown-item>
                    <el-date-picker
                      v-model="problemPieCustomDate"
                      type="daterange"
                      range-separator="-"
                      format="MM-DD"
                      value-format="YYYY-MM-DD"
                      placeholder="自定义"
                      @change="handleChartCustomDate('problemPie')"
                      style="width: 180px;"
                    />
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div ref="problemPieChart" style="height: 280px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 问题大类趋势 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">问题大类趋势（TOP5）</span>
              <el-button text size="small" class="card-setting-btn" @click="openChartSetting('problemTrend', '问题大类趋势', true)">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="chart-controls">
            <el-dropdown trigger="click" @command="(cmd) => handleAggregationChange('problem', cmd)">
              <el-button size="small">
                {{ problemAggregation === 'day' ? '按天' : '按周' }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="day">按天</el-dropdown-item>
                  <el-dropdown-item command="week">按周</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-dropdown trigger="click" @command="(cmd) => handleChartDateChange('problemTrend', cmd)">
              <el-button size="small">
                {{ problemTrendDateLabel }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="today">今日</el-dropdown-item>
                  <el-dropdown-item command="week">过去7天</el-dropdown-item>
                  <el-dropdown-item command="month">过去30天</el-dropdown-item>
                  <el-dropdown-item>
                    <el-date-picker
                      v-model="problemTrendCustomDate"
                      type="daterange"
                      range-separator="-"
                      format="MM-DD"
                      value-format="YYYY-MM-DD"
                      placeholder="自定义"
                      @change="handleChartCustomDate('problemTrend')"
                      style="width: 180px;"
                    />
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div ref="problemTrendChart" style="height: 280px;"></div>
        </el-card>
      </el-col>
      <!-- 问题子类分布 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">问题子类分布（TOP10）</span>
              <el-button text size="small" class="card-setting-btn" @click="openChartSetting('subProblemPie', '问题子类分布', false)">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="chart-controls">
            <el-dropdown trigger="click" @command="(cmd) => handleChartDateChange('subProblemPie', cmd)">
              <el-button size="small">
                {{ subProblemPieDateLabel }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="today">今日</el-dropdown-item>
                  <el-dropdown-item command="week">过去7天</el-dropdown-item>
                  <el-dropdown-item command="month">过去30天</el-dropdown-item>
                  <el-dropdown-item>
                    <el-date-picker
                      v-model="subProblemPieCustomDate"
                      type="daterange"
                      range-separator="-"
                      format="MM-DD"
                      value-format="YYYY-MM-DD"
                      placeholder="自定义"
                      @change="handleChartCustomDate('subProblemPie')"
                      style="width: 180px;"
                    />
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div ref="subProblemPieChart" style="height: 280px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 核心指标表格 -->
    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span class="card-title">核心指标汇总</span>
          <div class="card-header-right">
            <el-button text size="small" class="card-setting-btn" @click="openChartSetting('table', '核心指标汇总', true)">
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <el-button type="primary" size="small" @click="exportCSV">
              <el-icon><Download /></el-icon>
              导出CSV
            </el-button>
          </div>
        </div>
      </template>
      <div class="chart-controls">
        <el-dropdown trigger="click" @command="(cmd) => handleAggregationChange('table', cmd)">
          <el-button size="small">
            {{ tableAggregation === 'day' ? '按天' : tableAggregation === 'week' ? '按周' : '合计' }}
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="day">按天</el-dropdown-item>
              <el-dropdown-item command="week">按周</el-dropdown-item>
              <el-dropdown-item command="total">合计</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dropdown trigger="click" @command="(cmd) => handleChartDateChange('table', cmd)">
          <el-button size="small">
            {{ tableDateLabel }}
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="today">今日</el-dropdown-item>
              <el-dropdown-item command="week">过去7天</el-dropdown-item>
              <el-dropdown-item command="month">过去30天</el-dropdown-item>
              <el-dropdown-item>
                <el-date-picker
                  v-model="tableCustomDate"
                  type="daterange"
                  range-separator="-"
                  format="MM-DD"
                  value-format="YYYY-MM-DD"
                  placeholder="自定义"
                  @change="handleChartCustomDate('table')"
                  style="width: 180px;"
                />
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      <el-table :data="tableData" stripe style="width: 100%" max-height="400">
        <el-table-column prop="period" label="时间段" width="150" />
        <el-table-column prop="total" label="评价数" width="100" />
        <el-table-column prop="avgRating" label="平均星级" width="100">
          <template #default="{ row }">{{ row.avgRating?.toFixed(2) || '-' }}</template>
        </el-table-column>
        <el-table-column prop="positive" label="正向" width="80" />
        <el-table-column prop="negative" label="负向" width="80" />
        <el-table-column prop="neutral" label="中性" width="80" />
        <el-table-column prop="neutralNeg" label="中性偏负" width="100" />
        <el-table-column prop="negativeRate" label="负面占比" width="100">
          <template #default="{ row }">{{ row.negativeRate ? (row.negativeRate * 100).toFixed(1) + '%' : '-' }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 问题TOP10趋势 -->
    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span class="card-title">问题TOP10排名变化</span>
          <el-button text size="small" class="card-setting-btn" @click="openChartSetting('topProblem', '问题TOP10排名变化', true)">
            <el-icon><MoreFilled /></el-icon>
          </el-button>
        </div>
      </template>
      <div class="chart-controls">
        <el-dropdown trigger="click" @command="(cmd) => handleAggregationChange('topProblem', cmd)">
          <el-button size="small">
            {{ topProblemAggregation === 'day' ? '按天' : '按周' }}
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="day">按天</el-dropdown-item>
              <el-dropdown-item command="week">按周</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dropdown trigger="click" @command="(cmd) => handleChartDateChange('topProblem', cmd)">
          <el-button size="small">
            {{ topProblemDateLabel }}
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="today">今日</el-dropdown-item>
              <el-dropdown-item command="week">过去7天</el-dropdown-item>
              <el-dropdown-item command="month">过去30天</el-dropdown-item>
              <el-dropdown-item>
                <el-date-picker
                  v-model="topProblemCustomDate"
                  type="daterange"
                  range-separator="-"
                  format="MM-DD"
                  value-format="YYYY-MM-DD"
                  placeholder="自定义"
                  @change="handleChartCustomDate('topProblem')"
                  style="width: 180px;"
                />
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      <div ref="topProblemChart" style="height: 320px;"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Document, StarFilled, CircleCheck, CircleClose, Download, Calendar, ArrowDown, Refresh, MoreFilled, InfoFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

const props = defineProps(['data'])
const emit = defineEmits(['refresh'])

const STORAGE_KEY = 'realtime_data_settings'
const CHART_SETTINGS_KEY = 'realtime_chart_settings'

const lastRefreshTime = ref(new Date().toLocaleString('zh-CN'))
const isRefreshing = ref(false)

const chartSettingVisible = ref(false)
const chartSettingTitle = ref('')
const currentChartSetting = ref({
  chartKey: '',
  hasAggregation: false,
  aggregation: 'day',
  dateType: 'week'
})

const globalDateType = ref('week')
const globalDateRange = ref([])
const customDateRange = ref(null)

const trendAggregation = ref('day')
const trendDateType = ref('week')
const trendDateRange = ref([])
const trendCustomDate = ref(null)

const sentimentAggregation = ref('day')
const sentimentTrendDateType = ref('week')
const sentimentTrendDateRange = ref([])
const sentimentTrendCustomDate = ref(null)
const sentimentPieDateType = ref('week')
const sentimentPieDateRange = ref([])
const sentimentPieCustomDate = ref(null)

const problemAggregation = ref('day')
const problemTrendDateType = ref('week')
const problemTrendDateRange = ref([])
const problemTrendCustomDate = ref(null)
const problemPieDateType = ref('week')
const problemPieDateRange = ref([])
const problemPieCustomDate = ref(null)

const subProblemPieDateType = ref('week')
const subProblemPieDateRange = ref([])
const subProblemPieCustomDate = ref(null)

const tableAggregation = ref('day')
const tableDateType = ref('week')
const tableDateRange = ref([])
const tableCustomDate = ref(null)

const topProblemAggregation = ref('week')
const topProblemDateType = ref('week')
const topProblemDateRange = ref([])
const topProblemCustomDate = ref(null)

const trendChart = ref(null)
const sentimentPieChart = ref(null)
const sentimentTrendChart = ref(null)
const problemPieChart = ref(null)
const problemTrendChart = ref(null)
const subProblemPieChart = ref(null)
const topProblemChart = ref(null)

const tableData = ref([])

let trendChartInstance = null
let sentimentPieInstance = null
let sentimentTrendInstance = null
let problemPieInstance = null
let problemTrendInstance = null
let subProblemPieInstance = null
let topProblemInstance = null

const dateTypeLabels = {
  today: '今日',
  week: '过去7天',
  month: '过去30天',
  thisMonth: '本月',
  custom: '自定义'
}

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

const globalDateLabel = computed(() => dateTypeLabels[globalDateType.value] || '选择日期')
const trendDateLabel = computed(() => dateTypeLabels[trendDateType.value] || '选择日期')
const sentimentPieDateLabel = computed(() => dateTypeLabels[sentimentPieDateType.value] || '选择日期')
const sentimentTrendDateLabel = computed(() => dateTypeLabels[sentimentTrendDateType.value] || '选择日期')
const problemPieDateLabel = computed(() => dateTypeLabels[problemPieDateType.value] || '选择日期')
const problemTrendDateLabel = computed(() => dateTypeLabels[problemTrendDateType.value] || '选择日期')
const subProblemPieDateLabel = computed(() => dateTypeLabels[subProblemPieDateType.value] || '选择日期')
const tableDateLabel = computed(() => dateTypeLabels[tableDateType.value] || '选择日期')
const topProblemDateLabel = computed(() => dateTypeLabels[topProblemDateType.value] || '选择日期')

const metrics = computed(() => {
  if (!props.data?.reviews) return { total: 0, avgRating: 0, positive: 0, negative: 0 }
  
  let filteredReviews = props.data.reviews
  if (globalDateRange.value && globalDateRange.value.length === 2) {
    const [start, end] = globalDateRange.value
    filteredReviews = filteredReviews.filter(r => r['日期'] >= start && r['日期'] <= end)
  }
  
  const total = filteredReviews.length
  const avgRating = total > 0 ? filteredReviews.reduce((sum, r) => sum + (r['星级'] || 0), 0) / total : 0
  const positive = filteredReviews.filter(r => r['情感'] === '正向').length
  const negative = filteredReviews.filter(r => r['情感'] === '负向').length
  
  return { total, avgRating, positive, negative }
})

const handleGlobalDateCommand = (cmd) => {
  globalDateType.value = cmd
  globalDateRange.value = getDateRangeByType(cmd)
  syncAllDateRanges()
  saveSettings()
}

const handleCustomDateChange = () => {
  if (customDateRange.value && customDateRange.value.length === 2) {
    globalDateType.value = 'custom'
    globalDateRange.value = customDateRange.value
    syncAllDateRanges()
    saveSettings()
  }
}

const handleAggregationChange = (chart, cmd) => {
  switch (chart) {
    case 'trend':
      trendAggregation.value = cmd
      updateTrendChart()
      break
    case 'sentiment':
      sentimentAggregation.value = cmd
      updateSentimentTrendChart()
      break
    case 'problem':
      problemAggregation.value = cmd
      updateProblemTrendChart()
      break
    case 'table':
      tableAggregation.value = cmd
      updateTableData()
      break
    case 'topProblem':
      topProblemAggregation.value = cmd
      updateTopProblemChart()
      break
  }
  saveSettings()
}

const handleChartDateChange = (chart, cmd) => {
  const dateRange = getDateRangeByType(cmd)
  switch (chart) {
    case 'trend':
      trendDateType.value = cmd
      trendDateRange.value = dateRange
      updateTrendChart()
      break
    case 'sentimentPie':
      sentimentPieDateType.value = cmd
      sentimentPieDateRange.value = dateRange
      updateSentimentPieChart()
      break
    case 'sentimentTrend':
      sentimentTrendDateType.value = cmd
      sentimentTrendDateRange.value = dateRange
      updateSentimentTrendChart()
      break
    case 'problemPie':
      problemPieDateType.value = cmd
      problemPieDateRange.value = dateRange
      updateProblemPieChart()
      break
    case 'problemTrend':
      problemTrendDateType.value = cmd
      problemTrendDateRange.value = dateRange
      updateProblemTrendChart()
      break
    case 'subProblemPie':
      subProblemPieDateType.value = cmd
      subProblemPieDateRange.value = dateRange
      updateSubProblemPieChart()
      break
    case 'table':
      tableDateType.value = cmd
      tableDateRange.value = dateRange
      updateTableData()
      break
    case 'topProblem':
      topProblemDateType.value = cmd
      topProblemDateRange.value = dateRange
      updateTopProblemChart()
      break
  }
  saveSettings()
}

const handleChartCustomDate = (chart) => {
  let customDate = null
  let dateTypeRef = null
  let dateRangeRef = null
  let updateFn = null
  
  switch (chart) {
    case 'trend':
      customDate = trendCustomDate.value
      dateTypeRef = trendDateType
      dateRangeRef = trendDateRange
      updateFn = updateTrendChart
      break
    case 'sentimentPie':
      customDate = sentimentPieCustomDate.value
      dateTypeRef = sentimentPieDateType
      dateRangeRef = sentimentPieDateRange
      updateFn = updateSentimentPieChart
      break
    case 'sentimentTrend':
      customDate = sentimentTrendCustomDate.value
      dateTypeRef = sentimentTrendDateType
      dateRangeRef = sentimentTrendDateRange
      updateFn = updateSentimentTrendChart
      break
    case 'problemPie':
      customDate = problemPieCustomDate.value
      dateTypeRef = problemPieDateType
      dateRangeRef = problemPieDateRange
      updateFn = updateProblemPieChart
      break
    case 'problemTrend':
      customDate = problemTrendCustomDate.value
      dateTypeRef = problemTrendDateType
      dateRangeRef = problemTrendDateRange
      updateFn = updateProblemTrendChart
      break
    case 'subProblemPie':
      customDate = subProblemPieCustomDate.value
      dateTypeRef = subProblemPieDateType
      dateRangeRef = subProblemPieDateRange
      updateFn = updateSubProblemPieChart
      break
    case 'table':
      customDate = tableCustomDate.value
      dateTypeRef = tableDateType
      dateRangeRef = tableDateRange
      updateFn = updateTableData
      break
    case 'topProblem':
      customDate = topProblemCustomDate.value
      dateTypeRef = topProblemDateType
      dateRangeRef = topProblemDateRange
      updateFn = updateTopProblemChart
      break
  }
  
  if (customDate && customDate.length === 2 && dateTypeRef && dateRangeRef) {
    dateTypeRef.value = 'custom'
    dateRangeRef.value = customDate
    if (updateFn) updateFn()
    saveSettings()
  }
}

const syncAllDateRanges = () => {
  trendDateRange.value = [...globalDateRange.value]
  trendDateType.value = globalDateType.value
  sentimentPieDateRange.value = [...globalDateRange.value]
  sentimentPieDateType.value = globalDateType.value
  sentimentTrendDateRange.value = [...globalDateRange.value]
  sentimentTrendDateType.value = globalDateType.value
  problemPieDateRange.value = [...globalDateRange.value]
  problemPieDateType.value = globalDateType.value
  problemTrendDateRange.value = [...globalDateRange.value]
  problemTrendDateType.value = globalDateType.value
  subProblemPieDateRange.value = [...globalDateRange.value]
  subProblemPieDateType.value = globalDateType.value
  tableDateRange.value = [...globalDateRange.value]
  tableDateType.value = globalDateType.value
  topProblemDateRange.value = [...globalDateRange.value]
  topProblemDateType.value = globalDateType.value
  updateAllCharts()
  updateTableData()
}

const saveSettings = () => {
  const settings = {
    globalDateType: globalDateType.value,
    trendAggregation: trendAggregation.value,
    sentimentAggregation: sentimentAggregation.value,
    problemAggregation: problemAggregation.value,
    tableAggregation: tableAggregation.value,
    topProblemAggregation: topProblemAggregation.value
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
}

const loadSettings = () => {
  globalDateType.value = 'week'
  trendAggregation.value = 'day'
  sentimentAggregation.value = 'day'
  problemAggregation.value = 'day'
  tableAggregation.value = 'day'
  
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    const settings = JSON.parse(saved)
    if (settings.globalDateType) globalDateType.value = settings.globalDateType
    if (settings.trendAggregation) trendAggregation.value = settings.trendAggregation
    if (settings.sentimentAggregation) sentimentAggregation.value = settings.sentimentAggregation
    if (settings.problemAggregation) problemAggregation.value = settings.problemAggregation
    if (settings.tableAggregation) tableAggregation.value = settings.tableAggregation
    if (settings.topProblemAggregation) topProblemAggregation.value = settings.topProblemAggregation
  }
  
  globalDateRange.value = getDateRangeByType(globalDateType.value)
  syncAllDateRanges()
}

/**
 * 刷新数据
 */
const refreshData = async () => {
  isRefreshing.value = true
  emit('refresh')
  setTimeout(() => {
    lastRefreshTime.value = new Date().toLocaleString('zh-CN')
    isRefreshing.value = false
  }, 1000)
}

/**
 * 打开图表设置弹窗
 * @param {string} chartKey - 图表标识
 * @param {string} title - 弹窗标题
 * @param {boolean} hasAggregation - 是否有聚合选项
 */
const openChartSetting = (chartKey, title, hasAggregation) => {
  currentChartSetting.value = {
    chartKey,
    hasAggregation,
    aggregation: getChartAggregation(chartKey),
    dateType: getChartDateType(chartKey)
  }
  chartSettingTitle.value = title + ' - 默认设置'
  chartSettingVisible.value = true
}

/**
 * 获取图表当前聚合方式
 */
const getChartAggregation = (chartKey) => {
  switch (chartKey) {
    case 'trend': return trendAggregation.value
    case 'sentimentTrend': return sentimentAggregation.value
    case 'problemTrend': return problemAggregation.value
    case 'table': return tableAggregation.value
    case 'topProblem': return topProblemAggregation.value
    default: return 'day'
  }
}

/**
 * 获取图表当前日期类型
 */
const getChartDateType = (chartKey) => {
  switch (chartKey) {
    case 'trend': return trendDateType.value
    case 'sentimentPie': return sentimentPieDateType.value
    case 'sentimentTrend': return sentimentTrendDateType.value
    case 'problemPie': return problemPieDateType.value
    case 'problemTrend': return problemTrendDateType.value
    case 'subProblemPie': return subProblemPieDateType.value
    case 'table': return tableDateType.value
    case 'topProblem': return topProblemDateType.value
    default: return 'week'
  }
}

/**
 * 保存图表设置
 */
const saveChartSetting = () => {
  const { chartKey, hasAggregation, aggregation, dateType } = currentChartSetting.value
  
  const chartSettings = JSON.parse(localStorage.getItem(CHART_SETTINGS_KEY) || '{}')
  chartSettings[chartKey] = { aggregation, dateType }
  localStorage.setItem(CHART_SETTINGS_KEY, JSON.stringify(chartSettings))
  
  if (hasAggregation) {
    switch (chartKey) {
      case 'trend':
        trendAggregation.value = aggregation
        break
      case 'sentimentTrend':
        sentimentAggregation.value = aggregation
        break
      case 'problemTrend':
        problemAggregation.value = aggregation
        break
      case 'table':
        tableAggregation.value = aggregation
        break
      case 'topProblem':
        topProblemAggregation.value = aggregation
        break
    }
  }
  
  handleChartDateChange(chartKey, dateType)
  
  chartSettingVisible.value = false
  ElMessage.success('设置已保存')
}

/**
 * 加载图表设置
 */
const loadChartSettings = () => {
  const saved = localStorage.getItem(CHART_SETTINGS_KEY)
  if (saved) {
    const settings = JSON.parse(saved)
    
    if (settings.trend) {
      if (settings.trend.aggregation) trendAggregation.value = settings.trend.aggregation
      if (settings.trend.dateType) trendDateType.value = settings.trend.dateType
    }
    if (settings.sentimentPie && settings.sentimentPie.dateType) {
      sentimentPieDateType.value = settings.sentimentPie.dateType
    }
    if (settings.sentimentTrend) {
      if (settings.sentimentTrend.aggregation) sentimentAggregation.value = settings.sentimentTrend.aggregation
      if (settings.sentimentTrend.dateType) sentimentTrendDateType.value = settings.sentimentTrend.dateType
    }
    if (settings.problemPie && settings.problemPie.dateType) {
      problemPieDateType.value = settings.problemPie.dateType
    }
    if (settings.problemTrend) {
      if (settings.problemTrend.aggregation) problemAggregation.value = settings.problemTrend.aggregation
      if (settings.problemTrend.dateType) problemTrendDateType.value = settings.problemTrend.dateType
    }
    if (settings.subProblemPie && settings.subProblemPie.dateType) {
      subProblemPieDateType.value = settings.subProblemPie.dateType
    }
    if (settings.table) {
      if (settings.table.aggregation) tableAggregation.value = settings.table.aggregation
      if (settings.table.dateType) tableDateType.value = settings.table.dateType
    }
    if (settings.topProblem) {
      if (settings.topProblem.aggregation) topProblemAggregation.value = settings.topProblem.aggregation
      if (settings.topProblem.dateType) topProblemDateType.value = settings.topProblem.dateType
    }
  }
}

const getDateFilteredReviews = (dateRange) => {
  if (!props.data?.reviews) return []
  let reviews = props.data.reviews
  if (dateRange && dateRange.length === 2) {
    const [start, end] = dateRange
    reviews = reviews.filter(r => r['日期'] >= start && r['日期'] <= end)
  }
  return reviews
}

const groupByPeriod = (reviews, aggregation) => {
  const groups = {}
  reviews.forEach(r => {
    let key = r['日期']
    if (aggregation === 'week') {
      const d = new Date(r['日期'])
      const weekStart = new Date(d)
      weekStart.setDate(d.getDate() - d.getDay())
      key = weekStart.toISOString().split('T')[0]
    }
    if (!groups[key]) groups[key] = []
    groups[key].push(r)
  })
  return groups
}

/**
 * 计算折线图标签显示间隔
 * @param {number} dataLength - 数据点数量
 * @returns {number} - 间隔值，0表示全部显示
 */
const getLabelInterval = (dataLength) => {
  if (dataLength <= 7) return 0
  if (dataLength <= 14) return 1
  if (dataLength <= 30) return 2
  return Math.floor(dataLength / 10)
}

const updateTrendChart = () => {
  if (!trendChart.value || !props.data?.reviews) return
  
  const reviews = getDateFilteredReviews(trendDateRange.value)
  const groups = groupByPeriod(reviews, trendAggregation.value)
  
  const periods = Object.keys(groups).sort()
  const counts = periods.map(p => groups[p].length)
  const interval = getLabelInterval(counts.length)
  
  if (!trendChartInstance) trendChartInstance = echarts.init(trendChart.value)
  
  trendChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: periods, axisLabel: { rotate: 45 } },
    yAxis: { type: 'value' },
    series: [{
      data: counts,
      type: 'line',
      smooth: true,
      areaStyle: { opacity: 0.3 },
      itemStyle: { color: '#409eff' },
      label: {
        show: true,
        position: 'top',
        fontSize: 11,
        color: '#606266',
        formatter: '{c}',
        interval: interval
      }
    }],
    grid: { bottom: 60, right: 40, left: 50, top: 40 }
  })
}

const updateSentimentPieChart = () => {
  if (!sentimentPieChart.value || !props.data?.reviews) return
  
  const reviews = getDateFilteredReviews(sentimentPieDateRange.value)
  const sentimentCount = { '正向': 0, '负向': 0, '中性': 0, '中性偏负': 0 }
  reviews.forEach(r => {
    if (sentimentCount.hasOwnProperty(r['情感'])) sentimentCount[r['情感']]++
  })
  
  const data = Object.entries(sentimentCount)
    .filter(([_, v]) => v > 0)
    .map(([name, value]) => ({ name, value }))
  
  if (!sentimentPieInstance) sentimentPieInstance = echarts.init(sentimentPieChart.value)
  
  sentimentPieInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}条 ({d}%)' },
    legend: { bottom: '5%' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: {
        show: true,
        formatter: '{b}\n{d}%',
        fontSize: 12,
        color: '#606266'
      },
      labelLine: {
        show: true,
        length: 10,
        length2: 10
      },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      data,
      color: ['#67c23a', '#f56c6c', '#909399', '#e6a23c']
    }]
  })
}

const updateSentimentTrendChart = () => {
  if (!sentimentTrendChart.value || !props.data?.reviews) return
  
  const reviews = getDateFilteredReviews(sentimentTrendDateRange.value)
  const groups = groupByPeriod(reviews, sentimentAggregation.value)
  
  const periods = Object.keys(groups).sort()
  const sentimentTypes = ['正向', '负向', '中性', '中性偏负']
  const colors = ['#67c23a', '#f56c6c', '#909399', '#e6a23c']
  const interval = getLabelInterval(periods.length)
  
  const series = sentimentTypes.map((type, idx) => ({
    name: type,
    type: 'line',
    smooth: true,
    data: periods.map(p => groups[p].filter(r => r['情感'] === type).length),
    itemStyle: { color: colors[idx] },
    label: {
      show: true,
      position: 'top',
      fontSize: 10,
      color: colors[idx],
      formatter: '{c}',
      interval: interval
    }
  }))
  
  if (!sentimentTrendInstance) sentimentTrendInstance = echarts.init(sentimentTrendChart.value)
  
  sentimentTrendInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { bottom: '5%' },
    xAxis: { type: 'category', data: periods, axisLabel: { rotate: 45 } },
    yAxis: { type: 'value' },
    series,
    grid: { bottom: 80, right: 40, left: 50, top: 40 }
  })
}

const updateProblemPieChart = () => {
  if (!problemPieChart.value || !props.data?.reviews) return
  
  const reviews = getDateFilteredReviews(problemPieDateRange.value)
  const problemCount = {}
  reviews.forEach(r => {
    const problem = r['问题分类']?.split('-')[0]?.trim()
    if (problem && problem !== '无问题') {
      problemCount[problem] = (problemCount[problem] || 0) + 1
    }
  })
  
  const data = Object.entries(problemCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name, value]) => ({ name, value }))
  
  if (!problemPieInstance) problemPieInstance = echarts.init(problemPieChart.value)
  
  problemPieInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}条 ({d}%)' },
    legend: { type: 'scroll', bottom: '5%' },
    series: [{
      type: 'pie',
      radius: ['30%', '60%'],
      data,
      label: {
        show: true,
        formatter: '{b}\n{d}%',
        fontSize: 11,
        color: '#606266'
      },
      labelLine: {
        show: true,
        length: 8,
        length2: 8
      },
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  })
}

const updateProblemTrendChart = () => {
  if (!problemTrendChart.value || !props.data?.reviews) return
  
  const reviews = getDateFilteredReviews(problemTrendDateRange.value)
  const allProblemCount = {}
  reviews.forEach(r => {
    const problem = r['问题分类']?.split('-')[0]?.trim()
    if (problem && problem !== '无问题') {
      allProblemCount[problem] = (allProblemCount[problem] || 0) + 1
    }
  })
  
  const top5Problems = Object.entries(allProblemCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([name]) => name)
  
  const groups = groupByPeriod(reviews, problemAggregation.value)
  const periods = Object.keys(groups).sort()
  const interval = getLabelInterval(periods.length)
  
  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']
  const series = top5Problems.map((problem, idx) => ({
    name: problem,
    type: 'line',
    smooth: true,
    data: periods.map(p => groups[p].filter(r => r['问题分类']?.split('-')[0]?.trim() === problem).length),
    itemStyle: { color: colors[idx] },
    label: {
      show: true,
      position: 'top',
      fontSize: 10,
      color: colors[idx],
      formatter: '{c}',
      interval: interval
    }
  }))
  
  if (!problemTrendInstance) problemTrendInstance = echarts.init(problemTrendChart.value)
  
  problemTrendInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { bottom: '5%' },
    xAxis: { type: 'category', data: periods, axisLabel: { rotate: 45 } },
    yAxis: { type: 'value' },
    series,
    grid: { bottom: 80, right: 40, left: 50, top: 40 }
  })
}

const updateSubProblemPieChart = () => {
  if (!subProblemPieChart.value || !props.data?.reviews) return
  
  const reviews = getDateFilteredReviews(subProblemPieDateRange.value)
  const subProblemCount = {}
  reviews.forEach(r => {
    const parts = r['问题分类']?.split('-')
    if (parts && parts.length >= 2) {
      const subProblem = parts.slice(0, 2).join('-').trim()
      if (subProblem && !subProblem.includes('无问题')) {
        subProblemCount[subProblem] = (subProblemCount[subProblem] || 0) + 1
      }
    }
  })
  
  const data = Object.entries(subProblemCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name, value]) => ({ name, value }))
  
  if (!subProblemPieInstance) subProblemPieInstance = echarts.init(subProblemPieChart.value)
  
  subProblemPieInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}条 ({d}%)' },
    legend: { type: 'scroll', orient: 'vertical', right: '5%', top: 'middle' },
    series: [{
      type: 'pie',
      radius: ['30%', '60%'],
      center: ['35%', '50%'],
      data,
      label: {
        show: true,
        formatter: '{d}%',
        fontSize: 10,
        color: '#606266'
      },
      labelLine: {
        show: true,
        length: 5,
        length2: 5
      },
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  })
}

const updateTopProblemChart = () => {
  if (!topProblemChart.value || !props.data?.reviews) return
  
  const reviews = getDateFilteredReviews(topProblemDateRange.value)
  const groups = groupByPeriod(reviews, topProblemAggregation.value)
  const periods = Object.keys(groups).sort()
  const interval = getLabelInterval(periods.length)
  
  const allProblemCount = {}
  reviews.forEach(r => {
    const problem = r['问题分类']?.split('-')[0]?.trim()
    if (problem && problem !== '无问题') {
      allProblemCount[problem] = (allProblemCount[problem] || 0) + 1
    }
  })
  
  const top10Problems = Object.entries(allProblemCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name]) => name)
  
  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#48b8d0']
  const series = top10Problems.map((problem, idx) => ({
    name: problem,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    data: periods.map(p => groups[p].filter(r => r['问题分类']?.split('-')[0]?.trim() === problem).length),
    itemStyle: { color: colors[idx % colors.length] },
    label: {
      show: true,
      position: 'top',
      fontSize: 9,
      color: colors[idx % colors.length],
      formatter: '{c}',
      interval: interval
    }
  }))
  
  if (!topProblemInstance) topProblemInstance = echarts.init(topProblemChart.value)
  
  topProblemInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { type: 'scroll', bottom: '5%' },
    xAxis: { type: 'category', data: periods, axisLabel: { rotate: 45 } },
    yAxis: { type: 'value' },
    series,
    grid: { bottom: 100, right: 40, left: 50, top: 40 }
  })
}

const updateTableData = () => {
  if (!props.data?.reviews) return
  
  const reviews = getDateFilteredReviews(tableDateRange.value)
  
  if (tableAggregation.value === 'total') {
    const total = reviews.length
    const avgRating = total > 0 ? reviews.reduce((sum, r) => sum + (r['星级'] || 0), 0) / total : 0
    const positive = reviews.filter(r => r['情感'] === '正向').length
    const negative = reviews.filter(r => r['情感'] === '负向').length
    const neutral = reviews.filter(r => r['情感'] === '中性').length
    const neutralNeg = reviews.filter(r => r['情感'] === '中性偏负').length
    
    tableData.value = [{
      period: '合计',
      total,
      avgRating,
      positive,
      negative,
      neutral,
      neutralNeg,
      negativeRate: total > 0 ? negative / total : 0
    }]
  } else {
    const groups = groupByPeriod(reviews, tableAggregation.value)
    const periods = Object.keys(groups).sort()
    
    tableData.value = periods.map(period => {
      const groupReviews = groups[period]
      const total = groupReviews.length
      const avgRating = total > 0 ? groupReviews.reduce((sum, r) => sum + (r['星级'] || 0), 0) / total : 0
      const positive = groupReviews.filter(r => r['情感'] === '正向').length
      const negative = groupReviews.filter(r => r['情感'] === '负向').length
      const neutral = groupReviews.filter(r => r['情感'] === '中性').length
      const neutralNeg = groupReviews.filter(r => r['情感'] === '中性偏负').length
      
      return {
        period,
        total,
        avgRating,
        positive,
        negative,
        neutral,
        neutralNeg,
        negativeRate: total > 0 ? negative / total : 0
      }
    })
  }
}

const exportCSV = () => {
  if (tableData.value.length === 0) return
  
  const headers = ['时间段', '评价数', '平均星级', '正向', '负向', '中性', '中性偏负', '负面占比']
  const rows = tableData.value.map(row => [
    row.period,
    row.total,
    row.avgRating?.toFixed(2) || '',
    row.positive,
    row.negative,
    row.neutral,
    row.neutralNeg,
    row.negativeRate ? (row.negativeRate * 100).toFixed(1) + '%' : ''
  ])
  
  const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
  const BOM = '\uFEFF'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `舆情数据汇总_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

const updateAllCharts = () => {
  updateTrendChart()
  updateSentimentPieChart()
  updateSentimentTrendChart()
  updateProblemPieChart()
  updateProblemTrendChart()
  updateSubProblemPieChart()
  updateTopProblemChart()
}

watch(() => props.data, () => {
  if (props.data) {
    nextTick(() => {
      updateAllCharts()
      updateTableData()
    })
  }
}, { deep: true })

onMounted(() => {
  loadSettings()
  loadChartSettings()
  if (props.data) {
    nextTick(() => {
      updateAllCharts()
      updateTableData()
    })
  }
})
</script>

<style scoped>
.realtime-data {
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0;
}

.card-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.card-setting-btn {
  padding: 4px 8px;
  color: #909399;
}

.card-setting-btn:hover {
  color: #409eff;
  background-color: #ecf5ff;
}

.chart-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.setting-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f4f4f5;
  border-radius: 4px;
  color: #909399;
  font-size: 13px;
}

.setting-tip .el-icon {
  color: #409eff;
}
</style>
