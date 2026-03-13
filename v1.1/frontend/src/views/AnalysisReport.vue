<template>
  <div class="analysis-report">
    <!-- 生成新报告 -->
    <el-card shadow="hover">
      <template #header>
        <span>生成舆情分析报告</span>
      </template>
      <el-form :model="reportForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="reportForm.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="报告类型">
              <el-select v-model="reportForm.type" style="width: 100%;">
                <el-option label="周报" value="weekly" />
                <el-option label="月报" value="monthly" />
                <el-option label="自定义" value="custom" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item>
              <el-button type="primary" @click="generateReport" :loading="generating">
                <el-icon><Document /></el-icon>
                生成报告
              </el-button>
              <span class="tip">预计耗时30秒</span>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 当前报告内容 -->
    <el-card shadow="hover" style="margin-top: 20px;" v-if="currentReport">
      <template #header>
        <div class="card-header">
          <span>{{ currentReport.title }}</span>
          <div>
            <el-button type="primary" size="small" @click="downloadReport">
              <el-icon><Download /></el-icon>
              下载PDF
            </el-button>
            <el-button size="small" @click="refreshReport">
              <el-icon><Refresh /></el-icon>
              重新生成
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="report-content">
        <el-descriptions :column="4" border>
          <el-descriptions-item label="报告周期">{{ currentReport.period }}</el-descriptions-item>
          <el-descriptions-item label="生成时间">{{ currentReport.createTime }}</el-descriptions-item>
          <el-descriptions-item label="评价总数">{{ currentReport.totalReviews }}</el-descriptions-item>
          <el-descriptions-item label="负面占比">{{ currentReport.negativeRate }}%</el-descriptions-item>
        </el-descriptions>

        <div class="report-section">
          <h3>一、舆情概况</h3>
          <div class="section-content">{{ currentReport.summary }}</div>
        </div>

        <div class="report-section">
          <h3>二、情感趋势分析</h3>
          <div class="section-content">{{ currentReport.sentimentAnalysis }}</div>
        </div>

        <div class="report-section">
          <h3>三、主要问题及变化</h3>
          <el-table :data="currentReport.problems" stripe style="width: 100%">
            <el-table-column prop="category" label="问题分类" width="150" />
            <el-table-column prop="count" label="出现次数" width="100" />
            <el-table-column prop="trend" label="环比变化" width="100">
              <template #default="{ row }">
                <span :class="row.trend > 0 ? 'trend-up' : 'trend-down'">
                  {{ row.trend > 0 ? '↑' : '↓' }}{{ Math.abs(row.trend) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="suggestion" label="建议措施" />
          </el-table>
        </div>

        <div class="report-section">
          <h3>四、热点话题发现</h3>
          <div class="section-content">
            <el-tag v-for="topic in currentReport.hotTopics" :key="topic" style="margin-right: 10px; margin-bottom: 10px;">
              {{ topic }}
            </el-tag>
          </div>
        </div>

        <div class="report-section">
          <h3>五、建议措施</h3>
          <div class="section-content">{{ currentReport.suggestions }}</div>
        </div>
      </div>
    </el-card>

    <!-- 历史报告 -->
    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <span>历史报告</span>
      </template>
      <el-table :data="historyReports" stripe style="width: 100%">
        <el-table-column prop="period" label="报告周期" width="200" />
        <el-table-column prop="type" label="报告类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.type === 'weekly' ? '周报' : row.type === 'monthly' ? '月报' : '自定义' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="生成时间" width="180" />
        <el-table-column prop="totalReviews" label="评价数" width="100" />
        <el-table-column prop="negativeRate" label="负面占比" width="100">
          <template #default="{ row }">{{ row.negativeRate }}%</template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewReport(row)">查看</el-button>
            <el-button type="primary" link size="small" @click="downloadReportById(row)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Document, Download, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const reportForm = ref({
  dateRange: [],
  type: 'weekly'
})

const generating = ref(false)
const currentReport = ref(null)

const historyReports = ref([
  {
    id: 1,
    period: '2026-02-17 ~ 2026-02-23',
    type: 'weekly',
    createTime: '2026-02-23 15:30',
    totalReviews: 156,
    negativeRate: 23.5
  },
  {
    id: 2,
    period: '2026-02-10 ~ 2026-02-16',
    type: 'weekly',
    createTime: '2026-02-16 16:20',
    totalReviews: 142,
    negativeRate: 28.3
  },
  {
    id: 3,
    period: '2026-01-01 ~ 2026-01-31',
    type: 'monthly',
    createTime: '2026-02-01 10:00',
    totalReviews: 523,
    negativeRate: 25.1
  }
])

const generateReport = async () => {
  if (!reportForm.value.dateRange || reportForm.value.dateRange.length !== 2) {
    ElMessage.warning('请选择时间范围')
    return
  }
  
  generating.value = true
  
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  const [start, end] = reportForm.value.dateRange
  
  currentReport.value = {
    title: `舆情分析报告 (${start} ~ ${end})`,
    period: `${start} ~ ${end}`,
    createTime: new Date().toLocaleString('zh-CN'),
    totalReviews: 156,
    negativeRate: 23.5,
    summary: '本周期内共收到156条评价，其中负面评价占比23.5%，较上周下降4.8个百分点。整体舆情态势趋于平稳，玩家反馈以游戏体验优化建议为主。主要关注点集中在服务器稳定性、新角色平衡性等方面。',
    sentimentAnalysis: '情感分布方面，正向评价占比35.2%，中性评价占比41.3%，负面评价占比23.5%。负面评价主要集中在游戏卡顿、匹配机制等问题。与上周相比，正向评价占比提升3.2%，负面评价占比下降4.8%，整体情感趋势向好。',
    problems: [
      { category: '服务器问题', count: 28, trend: -15, suggestion: '建议加强服务器扩容，优化网络连接' },
      { category: '游戏卡顿', count: 22, trend: 8, suggestion: '建议优化客户端性能，减少内存占用' },
      { category: '匹配机制', count: 18, trend: -5, suggestion: '建议优化匹配算法，平衡玩家水平' },
      { category: '新角色平衡', count: 15, trend: 25, suggestion: '建议调整新角色数值，保持游戏平衡' },
      { category: '环境问题', count: 12, trend: -20, suggestion: '建议加强举报机制，净化游戏环境' }
    ],
    hotTopics: ['新角色上线', '春节活动', '排位赛季', '外挂问题', '新手引导'],
    suggestions: '1. 建议优先解决服务器稳定性问题，这是玩家反馈最多的痛点。\n2. 新角色平衡性需要持续关注，建议收集更多数据后进行微调。\n3. 加强对游戏环境的治理，提升玩家体验。\n4. 考虑优化新手引导流程，降低新玩家流失率。\n5. 建议定期发布优化公告，增强玩家信任。'
  }
  
  generating.value = false
  ElMessage.success('报告生成成功')
}

const viewReport = (row) => {
  currentReport.value = {
    title: `舆情分析报告 (${row.period})`,
    period: row.period,
    createTime: row.createTime,
    totalReviews: row.totalReviews,
    negativeRate: row.negativeRate,
    summary: '历史报告内容...',
    sentimentAnalysis: '历史报告情感分析...',
    problems: [],
    hotTopics: [],
    suggestions: '历史报告建议...'
  }
}

const downloadReport = () => {
  ElMessage.info('PDF下载功能开发中...')
}

const downloadReportById = (row) => {
  ElMessage.info(`下载报告: ${row.period}`)
}

const refreshReport = () => {
  generateReport()
}

onMounted(() => {
  const today = new Date()
  const weekAgo = new Date(today)
  weekAgo.setDate(weekAgo.getDate() - 7)
  const formatDate = (d) => d.toISOString().split('T')[0]
  
  reportForm.value.dateRange = [formatDate(weekAgo), formatDate(today)]
})
</script>

<style scoped>
.analysis-report {
  padding: 0;
}

.tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-content {
  padding: 10px 0;
}

.report-section {
  margin-top: 25px;
}

.report-section h3 {
  color: #303133;
  border-left: 4px solid #409eff;
  padding-left: 10px;
  margin-bottom: 15px;
}

.section-content {
  line-height: 1.8;
  color: #606266;
  white-space: pre-wrap;
}

.trend-up {
  color: #f56c6c;
}

.trend-down {
  color: #67c23a;
}
</style>
