<template>
  <div class="system-monitor">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover" class="status-card">
          <div class="status-icon success" v-if="systemStatus === 'running'">
            <el-icon><SuccessFilled /></el-icon>
          </div>
          <div class="status-icon warning" v-else-if="systemStatus === 'warning'">
            <el-icon><WarningFilled /></el-icon>
          </div>
          <div class="status-icon error" v-else>
            <el-icon><CircleCloseFilled /></el-icon>
          </div>
          <div class="status-text">
            <div class="label">系统状态</div>
            <div class="value">{{ statusText }}</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="status-card">
          <div class="status-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="status-text">
            <div class="label">下次执行</div>
            <div class="value">{{ nextRunTime }}</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="status-card">
          <div class="status-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="status-text">
            <div class="label">今日处理</div>
            <div class="value">{{ todayProcessed }} 条</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="status-card">
          <div class="status-icon" :class="tokenUsageClass">
            <el-icon><Coin /></el-icon>
          </div>
          <div class="status-text">
            <div class="label">Token消耗</div>
            <div class="value">{{ tokenUsage }}%</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>Token消耗监控</span>
          <el-tag :type="tokenUsageClass" size="small">{{ dailyTokens }} / {{ dailyLimit }}</el-tag>
        </div>
      </template>
      <el-progress 
        :percentage="tokenUsagePercent" 
        :status="tokenProgressStatus"
        :stroke-width="20"
        :text-inside="true"
      />
      <div class="token-info">
        <span>预估费用: ¥{{ estimatedCost }}</span>
        <span>剩余可分析: ~{{ remainingReviews }} 条</span>
      </div>
    </el-card>
    
    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>爬虫任务监控</span>
          <div class="header-actions">
            <el-button 
              type="danger" 
              size="small"
              :disabled="!crawlerStatus.running"
              @click="stopCrawler"
            >
              <el-icon><VideoPause /></el-icon>
              终止任务
            </el-button>
            <el-button type="primary" size="small" @click="refreshAll">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      
      <el-descriptions :column="4" border v-if="crawlerStatus.running || crawlerStatus.product">
        <el-descriptions-item label="任务状态">
          <el-tag :type="crawlerStatus.running ? 'success' : 'info'">
            {{ crawlerStatus.running ? '运行中' : '空闲' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="当前产品">{{ crawlerStatus.product || '-' }}</el-descriptions-item>
        <el-descriptions-item label="已爬取">{{ crawlerStatus.crawled || 0 }} 条</el-descriptions-item>
        <el-descriptions-item label="已分析">{{ crawlerStatus.analyzed || 0 }} 条</el-descriptions-item>
      </el-descriptions>
      
      <div v-if="crawlerStatus.running" class="progress-section">
        <div class="progress-label">爬取进度</div>
        <el-progress :percentage="crawlProgress" :status="'success'" />
      </div>
      
      <div v-if="crawlerStatus.logs && crawlerStatus.logs.length > 0" class="task-logs">
        <div class="log-item" v-for="(log, index) in crawlerStatus.logs" :key="index">
          <span class="log-time">{{ formatTime(log.time) }}</span>
          <span :class="['log-' + log.type]">{{ log.message }}</span>
        </div>
      </div>
      
      <el-empty v-if="!crawlerStatus.running && !crawlerStatus.product" description="暂无运行中的任务" />
    </el-card>
    
    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>任务执行日志</span>
        </div>
      </template>
      
      <el-table :data="taskLogs" stripe style="width: 100%" max-height="400">
        <el-table-column prop="timestamp" label="执行时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="爬取" width="80">
          <template #default="{ row }">
            {{ row.steps?.crawl?.count || 0 }} 条
          </template>
        </el-table-column>
        <el-table-column label="分析" width="80">
          <template #default="{ row }">
            {{ row.steps?.analyze?.count || 0 }} 条
          </template>
        </el-table-column>
        <el-table-column label="Token" width="100">
          <template #default="{ row }">
            {{ row.steps?.analyze?.token_used || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="100">
          <template #default="{ row }">
            {{ row.duration ? row.duration.toFixed(1) + 's' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="message" label="备注">
          <template #default="{ row }">
            {{ row.message || row.error || '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>告警设置</span>
          <el-switch v-model="alertEnabled" active-text="开启" inactive-text="关闭" />
        </div>
      </template>
      
      <el-form :model="alertForm" label-width="120px" :disabled="!alertEnabled">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="Token告警阈值">
              <el-input-number v-model="alertForm.tokenThreshold" :min="50" :max="100" />
              <span class="unit">%</span>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="任务失败告警">
              <el-switch v-model="alertForm.taskFailAlert" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="告警方式">
              <el-select v-model="alertForm.alertMethod" style="width: 100%;">
                <el-option label="页面提示" value="page" />
                <el-option label="邮件通知" value="email" />
                <el-option label="企业微信" value="wechat" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { SuccessFilled, WarningFilled, CircleCloseFilled, Clock, Document, Coin, Refresh, VideoPause } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElNotification, ElMessageBox } from 'element-plus'

const systemStatus = ref('running')
const statusText = computed(() => {
  const statusMap = {
    'running': '运行中',
    'warning': '警告',
    'error': '异常',
    'stopped': '已停止'
  }
  return statusMap[systemStatus.value] || '未知'
})

const nextRunTime = ref('--:--')
const todayProcessed = ref(0)

const dailyTokens = ref(0)
const dailyLimit = ref(100000)
const estimatedCost = ref('0.00')

const tokenUsagePercent = computed(() => {
  return Math.min(100, Math.round(dailyTokens.value / dailyLimit.value * 100))
})

const tokenUsage = computed(() => tokenUsagePercent.value)

const tokenUsageClass = computed(() => {
  if (tokenUsagePercent.value >= 90) return 'error'
  if (tokenUsagePercent.value >= 70) return 'warning'
  return 'success'
})

const tokenProgressStatus = computed(() => {
  if (tokenUsagePercent.value >= 90) return 'exception'
  if (tokenUsagePercent.value >= 70) return 'warning'
  return 'success'
})

const remainingReviews = computed(() => {
  const tokensPerReview = 320
  return Math.max(0, Math.floor((dailyLimit.value - dailyTokens.value) / tokensPerReview))
})

const taskLogs = ref([])

const crawlerStatus = ref({
  running: false,
  product: null,
  crawled: 0,
  analyzed: 0,
  total: 0,
  logs: []
})

const crawlProgress = computed(() => {
  if (crawlerStatus.value.total === 0) return 0
  return Math.round(crawlerStatus.value.crawled / crawlerStatus.value.total * 100)
})

const alertEnabled = ref(true)
const alertForm = ref({
  tokenThreshold: 80,
  taskFailAlert: true,
  alertMethod: 'page'
})

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

const refreshMonitorStatus = async () => {
  try {
    const response = await axios.get('/api/monitor/status')
    const data = response.data
    
    systemStatus.value = data.system_status || 'running'
    nextRunTime.value = data.next_run_time || '--:--'
    todayProcessed.value = data.today_processed || 0
    dailyTokens.value = data.daily_tokens || 0
    estimatedCost.value = data.estimated_cost || '0.00'
    taskLogs.value = data.task_logs || []
    
    checkAlerts()
    
  } catch (error) {
    console.error('获取监控数据失败:', error)
  }
}

const refreshCrawlerStatus = async () => {
  try {
    const response = await axios.get('/api/crawler/status')
    crawlerStatus.value = response.data
  } catch (error) {
    console.error('获取爬虫状态失败:', error)
    ElMessage.error('获取爬虫状态失败：' + (error.response?.data?.detail || error.message))
  }
}

const refreshAll = async () => {
  await Promise.all([refreshMonitorStatus(), refreshCrawlerStatus()])
  ElMessage.success('刷新成功')
}

const stopCrawler = async () => {
  try {
    await ElMessageBox.confirm('确定要终止当前任务吗？', '确认终止', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await axios.post('/api/crawler/stop')
    ElMessage.success('任务已终止')
    refreshCrawlerStatus()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('终止失败：' + (error.response?.data?.detail || error.message))
    }
  }
}

const checkAlerts = () => {
  if (!alertEnabled.value) return
  
  if (tokenUsagePercent.value >= alertForm.value.tokenThreshold) {
    showAlert('warning', 'Token消耗告警', `Token使用已达 ${tokenUsagePercent.value}%，请注意控制`)
  }
  
  if (alertForm.value.taskFailAlert) {
    const lastLog = taskLogs.value[0]
    if (lastLog && lastLog.status === 'failed') {
      showAlert('error', '任务执行失败', lastLog.error || '请检查系统日志')
    }
  }
}

const showAlert = (type, title, message) => {
  if (alertForm.value.alertMethod === 'page') {
    ElNotification({
      title,
      message,
      type,
      duration: 0
    })
  }
}

let refreshTimer = null

onMounted(() => {
  refreshAll()
  refreshTimer = setInterval(refreshAll, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.system-monitor {
  padding: 0;
}

.status-card {
  display: flex;
  align-items: center;
  padding: 10px;
}

.status-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  width: 100%;
}

.status-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-right: 15px;
  background: #f0f2f5;
  color: #909399;
}

.status-icon.success {
  background: #e1f3d8;
  color: #67c23a;
}

.status-icon.warning {
  background: #fdf6ec;
  color: #e6a23c;
}

.status-icon.error {
  background: #fde2e2;
  color: #f56c6c;
}

.status-text {
  flex: 1;
}

.status-text .label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.status-text .value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.token-info {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}

.unit {
  margin-left: 5px;
  color: #909399;
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
</style>
