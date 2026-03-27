<template>
  <div class="data-update">
    <el-card class="status-card">
      <template #header>
        <div class="card-header">
          <span>数据状态</span>
          <el-button type="primary" size="small" @click="refreshStatus" :loading="loading">
            刷新状态
          </el-button>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic title="总评价数" :value="status.total_reviews || 0" />
        </el-col>
        <el-col :span="6">
          <div class="status-item">
            <div class="status-label">最新评价日期</div>
            <div class="status-value" :class="{'text-warning': !status.last_review_date || status.last_review_date === '无数据'}">
              {{ status.last_review_date || '无数据' }}
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <el-statistic title="缺失天数" :value="status.gap_days || 0" />
        </el-col>
        <el-col :span="6">
          <div class="status-item">
            <div class="status-label">最后爬取状态</div>
            <div class="status-value">
              <el-tag :type="getStatusType(status.last_crawl_status)" size="small">
                {{ getStatusText(status.last_crawl_status) }}
              </el-tag>
            </div>
          </div>
        </el-col>
      </el-row>
      
      <div v-if="status.gap_dates && status.gap_dates.length > 0" class="gap-info">
        <el-alert type="warning" :closable="false">
          <template #title>
            <span>检测到 {{ status.gap_days }} 天数据缺失</span>
          </template>
          <div class="gap-dates">
            缺失日期：{{ status.gap_dates.join(', ') }}
            <span v-if="status.gap_days > 10">等 {{ status.gap_days }} 天</span>
          </div>
        </el-alert>
      </div>
    </el-card>

    <el-card class="control-card">
      <template #header>
        <span>数据更新</span>
      </template>
      
      <el-form :model="form" label-width="100px">
        <el-form-item label="选择产品">
          <el-select v-model="form.product_id" placeholder="请选择产品" style="width: 200px" @change="refreshStatus">
            <el-option
              v-for="product in products"
              :key="product.id"
              :label="product.name"
              :value="product.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="form.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 300px"
          />
          <span class="form-tip">增量更新和自动补漏时使用</span>
        </el-form-item>
        
        <el-form-item>
          <el-space wrap>
            <el-button type="primary" @click="crawlFull" :loading="crawling" :disabled="!isAdmin">
              全量爬取
            </el-button>
            <el-button type="success" @click="crawlIncremental" :loading="crawling">
              增量更新
            </el-button>
            <el-button type="warning" @click="fillGaps" :loading="crawling">
              自动补漏
            </el-button>
          </el-space>
          <el-space wrap style="margin-left: 12px;">
            <el-select v-model="autoUpdateInterval" style="width: 120px;">
              <el-option :value="1" label="1分钟" />
              <el-option :value="5" label="5分钟" />
              <el-option :value="10" label="10分钟" />
              <el-option :value="30" label="30分钟" />
              <el-option :value="60" label="1小时" />
              <el-option :value="120" label="2小时" />
              <el-option :value="360" label="6小时" />
              <el-option :value="720" label="12小时" />
              <el-option :value="1440" label="24小时" />
            </el-select>
            <el-button type="info" @click="startAutoUpdate" :loading="crawling">
              启动自动更新
            </el-button>
            <el-button type="danger" @click="stopAutoUpdate" :loading="crawling">
              停止自动更新
            </el-button>
          </el-space>
          <div v-if="!isAdmin" class="admin-tip">
            <el-icon><WarningFilled /></el-icon>
            全量爬取需要管理员权限
          </div>
          <div class="form-tip" style="margin-top: 8px;">
            自动更新状态：{{ autoUpdateStatus.running ? '运行中' : '已停止' }}，
            间隔 {{ autoUpdateStatus.interval_minutes || 120 }} 分钟
          </div>
        </el-form-item>
      </el-form>
      
      <el-divider />
      
      <div class="mode-description">
        <h4>模式说明</h4>
        <ul>
          <li><strong>全量爬取</strong>：一次性爬取所有历史数据，适合首次爬取或重新爬取（需要管理员权限）</li>
          <li><strong>增量更新</strong>：从最后爬取日期开始，继续爬到今天，适合定期更新</li>
          <li><strong>自动补漏</strong>：检测最近30天内缺失的日期，自动补齐数据</li>
        </ul>
      </div>
    </el-card>

    <el-card class="task-card">
      <template #header>
        <div class="card-header">
          <span>当前任务状态</span>
          <el-button 
            type="danger" 
            size="small"
            :disabled="!taskStatus.running"
            @click="stopTask"
          >
            <el-icon><VideoPause /></el-icon>
            终止任务
          </el-button>
        </div>
      </template>
      
      <el-descriptions :column="4" border v-if="taskStatus.running || taskStatus.product">
        <el-descriptions-item label="任务状态">
          <el-tag :type="taskStatus.running ? 'success' : 'info'">
            {{ taskStatus.running ? '运行中' : '空闲' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="当前产品">{{ taskStatus.product || '-' }}</el-descriptions-item>
        <el-descriptions-item label="已爬取">{{ taskStatus.crawled || 0 }} 条</el-descriptions-item>
        <el-descriptions-item label="已分析">{{ taskStatus.analyzed || 0 }} 条</el-descriptions-item>
      </el-descriptions>
      
      <div v-if="taskStatus.running" class="progress-section">
        <div class="progress-label">爬取进度</div>
        <el-progress :percentage="crawlProgress" :status="'success'" />
      </div>
      
      <div v-if="taskStatus.logs && taskStatus.logs.length > 0" class="task-logs">
        <div class="log-item" v-for="(log, index) in taskStatus.logs" :key="index">
          <span class="log-time">{{ formatTime(log.time) }}</span>
          <span :class="['log-' + log.type]">{{ log.message }}</span>
        </div>
      </div>
      
      <!-- 任务结果显示 -->
      <div v-if="!taskStatus.running && taskStatus.logs && taskStatus.logs.length > 0" class="task-result">
        <el-divider />
        <h4>上次任务结果</h4>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="任务类型">
            {{ taskStatus.product || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="完成时间">
            {{ formatTime(taskStatus.logs[taskStatus.logs.length - 1]?.time) }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="taskStatus.logs[taskStatus.logs.length - 1]?.type === 'success' ? 'success' : 'danger'">
              {{ taskStatus.logs[taskStatus.logs.length - 1]?.type === 'success' ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <div class="result-message" v-if="taskStatus.logs[taskStatus.logs.length - 1]?.message">
          {{ taskStatus.logs[taskStatus.logs.length - 1]?.message }}
        </div>
      </div>
      
      <el-empty v-if="!taskStatus.running && !taskStatus.product && (!taskStatus.logs || taskStatus.logs.length === 0)" description="暂无运行中的任务" />
    </el-card>

    <el-card class="log-card">
      <template #header>
        <span>爬取日志</span>
      </template>
      
      <el-table :data="logs" style="width: 100%" max-height="300">
        <el-table-column prop="start_time" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="spider_name" label="爬取模式" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reviews_added" label="新增" width="80" />
        <el-table-column prop="reviews_updated" label="重复" width="80" />
        <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { WarningFilled, VideoPause } from '@element-plus/icons-vue'
import api from '../api'


const loading = ref(false)
const crawling = ref(false)

const status = ref({
  total_reviews: 0,
  last_review_date: null,
  last_crawl_date: null,
  last_crawl_status: null,
  gap_days: 0,
  gap_dates: []
})

const logs = ref([])
const products = ref([])

const form = ref({
  product_id: 1,
  dateRange: null
})

const taskStatus = ref({
  running: false,
  product: null,
  crawled: 0,
  analyzed: 0,
  total: 0,
  logs: []
})
const autoUpdateStatus = ref({
  running: false,
  interval_minutes: 120
})
const autoUpdateInterval = ref(120)

const isAdmin = ref(true)

const crawlProgress = computed(() => {
  if (taskStatus.value.total === 0) return 0
  return Math.round(taskStatus.value.crawled / taskStatus.value.total * 100)
})

const getStatusType = (status) => {
  if (!status) return 'info'
  const typeMap = {
    'success': 'success',
    'running': 'primary',
    'failed': 'danger',
    '无记录': 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  if (!status) return '无记录'
  const textMap = {
    'success': '成功',
    'running': '运行中',
    'failed': '失败',
    '无记录': '无记录'
  }
  return textMap[status] || status
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

const refreshStatus = async () => {
  loading.value = true
  try {
    const res = await api.get('/data-status', {
      params: { product_id: form.value.product_id }
    })
    status.value = res.data
  } catch (error) {
    console.error('获取状态失败：', error)
    ElMessage.error('获取状态失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const getProducts = async () => {
  try {
    const res = await api.get('/products')
    products.value = res.data.products || []
    if (products.value.length > 0 && !form.value.product_id) {
      form.value.product_id = products.value[0].id
    }
  } catch (error) {
    console.error('获取产品列表失败：', error)
  }
}

const getLogs = async () => {
  try {
    const res = await api.get('/crawl-logs', {
      params: { 
        product_id: form.value.product_id,
        limit: 20 
      }
    })
    logs.value = res.data.logs || []
  } catch (error) {
    console.error('获取日志失败：', error)
  }
}

const pollTaskStatus = async () => {
  try {
    const res = await api.get('/crawler/status')
    taskStatus.value = res.data
  } catch (error) {
    console.error('获取任务状态失败：', error)
  }
}

const confirmAction = async (action, description) => {
  if (action === 'full' && !isAdmin.value) {
    ElMessage.warning('全量爬取需要管理员权限')
    return false
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要执行${description}吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    return true
  } catch {
    return false
  }
}

const crawlFull = async () => {
  if (!await confirmAction('full', '全量爬取')) return
  
  crawling.value = true
  try {
    const res = await api.post('/crawler/start', null, {
      params: {
        product_id: form.value.product_id
      }
    })
    ElMessage.success(res.data.message || '爬虫任务已启动')
    startPolling()
  } catch (error) {
    ElMessage.error('启动爬取失败：' + (error.response?.data?.detail || error.message))
  } finally {
    crawling.value = false
  }
}

const crawlIncremental = async () => {
  if (!await confirmAction('incremental', '增量更新')) return
  
  crawling.value = true
  try {
    let params = { product_id: form.value.product_id }
    if (form.value.dateRange && form.value.dateRange.length === 2) {
      params.start_date = form.value.dateRange[0]
      params.end_date = form.value.dateRange[1]
    }
    
    const res = await api.post('/crawler/incremental', null, { params })
    ElMessage.success(res.data.message || '增量更新已启动')
    startPolling()
  } catch (error) {
    ElMessage.error('启动更新失败：' + (error.response?.data?.detail || error.message))
  } finally {
    crawling.value = false
  }
}

const fillGaps = async () => {
  if (!await confirmAction('fill', '自动补漏')) return
  
  crawling.value = true
  try {
    const res = await api.post('/crawler/fill-gaps', null, {
      params: { product_id: form.value.product_id }
    })
    if (res.data.status === 'skipped') {
      ElMessage.info(res.data.message)
    } else {
      ElMessage.success(res.data.message || '补漏任务已启动')
      startPolling()
    }
  } catch (error) {
    ElMessage.error('启动补漏失败：' + (error.response?.data?.detail || error.message))
  } finally {
    crawling.value = false
  }
}

const stopTask = async () => {
  try {
    await ElMessageBox.confirm('确定要终止当前任务吗？', '确认终止', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.post('/crawler/stop')
    ElMessage.success('任务已终止')
    stopPolling()
    refreshStatus()
    getLogs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('终止失败：' + (error.response?.data?.detail || error.message))
    }
  }
}

const fetchAutoUpdateStatus = async () => {
  try {
    const res = await api.get('/auto-update/status')
    autoUpdateStatus.value = res.data.status || { running: false, interval_minutes: 120 }
  } catch (error) {
    console.error('获取自动更新状态失败：', error)
  }
}

const startAutoUpdate = async () => {
  if (!await confirmAction('auto', '启动自动更新')) return
  crawling.value = true
  try {
    const res = await api.post('/auto-update/start', null, {
      params: {
        product_id: form.value.product_id,
        interval_minutes: autoUpdateInterval.value
      }
    })
    ElMessage.success(res.data.message || '自动更新已启动')
    await fetchAutoUpdateStatus()
  } catch (error) {
    ElMessage.error('启动自动更新失败：' + (error.response?.data?.detail || error.message))
  } finally {
    crawling.value = false
  }
}

const stopAutoUpdate = async () => {
  if (!await confirmAction('auto', '停止自动更新')) return
  crawling.value = true
  try {
    const res = await api.post('/auto-update/stop')
    ElMessage.success(res.data.message || '自动更新已停止')
    await fetchAutoUpdateStatus()
  } catch (error) {
    ElMessage.error('停止自动更新失败：' + (error.response?.data?.detail || error.message))
  } finally {
    crawling.value = false
  }
}

let pollTimer = null
let lastTaskRunning = false

const startPolling = () => {
  if (pollTimer) clearInterval(pollTimer)
  pollTaskStatus()
  lastTaskRunning = !!taskStatus.value.running
  pollTimer = setInterval(async () => {
    await pollTaskStatus()
    await getLogs()
    
    // 检测任务从运行中变为完成
    if (lastTaskRunning && !taskStatus.value.running) {
      // 任务完成，刷新日志和状态
      await getLogs()
      await refreshStatus()
      
      // 显示任务完成通知
      const lastLog = taskStatus.value.logs?.[taskStatus.value.logs.length - 1]
      if (lastLog && lastLog.type === 'success') {
        ElMessage.success(`任务完成：${lastLog.message}`)
      }
    }
    lastTaskRunning = taskStatus.value.running
  }, 2000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(async () => {
  await getProducts()
  await refreshStatus()
  await getLogs()
  await fetchAutoUpdateStatus()
  await pollTaskStatus()
  if (taskStatus.value.running) {
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.data-update {
  padding: 0;
}

.status-card, .control-card, .task-card, .log-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-item {
  text-align: center;
  padding: 10px 0;
}

.status-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.status-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.gap-info {
  margin-top: 20px;
}

.gap-dates {
  margin-top: 10px;
  font-size: 13px;
}

.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

.admin-tip {
  margin-top: 10px;
  color: #e6a23c;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.mode-description {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
}

.mode-description h4 {
  margin: 0 0 10px 0;
}

.mode-description ul {
  margin: 0;
  padding-left: 20px;
}

.mode-description li {
  margin: 5px 0;
  color: #606266;
  font-size: 13px;
}

.text-warning {
  color: #e6a23c;
}

.progress-section {
  margin-top: 15px;
}

.progress-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 5px;
}

.task-logs {
  margin-top: 15px;
  max-height: 200px;
  overflow-y: auto;
  background: #f5f7fa;
  border-radius: 4px;
  padding: 10px;
}

.log-item {
  font-size: 12px;
  margin-bottom: 5px;
}

.log-time {
  color: #909399;
  margin-right: 10px;
}

.log-success { color: #67c23a; }
.log-error { color: #f56c6c; }
.log-warning { color: #e6a23c; }
.log-info { color: #409eff; }

.task-result {
  margin-top: 15px;
  padding: 15px;
  background: #f0f9ff;
  border-radius: 4px;
  border: 1px solid #d9ecff;
}

.task-result h4 {
  margin: 0 0 15px 0;
  color: #409eff;
}

.result-message {
  margin-top: 10px;
  padding: 10px;
  background: #fff;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
}
</style>
