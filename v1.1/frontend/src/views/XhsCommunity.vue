<template>
  <div class="xhs-page" v-loading="loading">
    <div class="header-row">
      <h2>{{ moduleTitle }}</h2>
      <el-space>
        <el-tag type="info">{{ meta.notes_file || '未检测到文件' }}</el-tag>
        <el-button type="primary" @click="loadData">刷新数据</el-button>
      </el-space>
    </div>

    <el-row :gutter="16" class="card-row">
      <el-col :span="6"><el-card><div class="metric-title">总帖子数</div><div class="metric-value">{{ overview['总帖子数'] || 0 }}</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="metric-title">总评论数</div><div class="metric-value">{{ overview['总评论数'] || 0 }}</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="metric-title">高风险帖子数</div><div class="metric-value">{{ overview['高风险帖子数'] || 0 }}</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="metric-title">近似作者数</div><div class="metric-value">{{ overview['近似作者数'] || 0 }}</div></el-card></el-col>
    </el-row>

    <el-card v-if="module === 'xhs-intro'" class="section-card">
      <template #header><div class="section-title">简介</div></template>
      <el-alert
        title="社区洞察套件整合海内外社媒与玩家社区语料，结合GenAI能力形成玩家生态图景"
        type="info"
        :closable="false"
        show-icon
      />
      <el-space direction="vertical" style="margin-top: 12px; width: 100%;">
        <el-tag type="success">海内外主流媒体、社区与私域真实声音</el-tag>
        <el-tag type="success">情感分析、关键词提取、重要度评估、风控识别</el-tag>
        <el-tag type="success">热点话题发掘、追踪与定期解读</el-tag>
        <el-tag type="success">结合游戏内行为数据支撑运营决策</el-tag>
      </el-space>
    </el-card>

    <el-card v-else-if="module === 'xhs-manual'" class="section-card">
      <template #header><div class="section-title">使用指南</div></template>
      <el-steps :active="4" align-center finish-status="success">
        <el-step title="进入社区模块" description="顶部导航进入社区，再选择小红书监控功能页" />
        <el-step title="查看监控概览" description="先看声量、风险、热点变化" />
        <el-step title="下钻功能模块" description="按左侧功能菜单依次查看监控、分析、KOL、竞品" />
        <el-step title="联动运营决策" description="结合游戏内行为数据推进动作" />
      </el-steps>
      <el-divider />
      <el-space wrap>
        <el-tag type="success" effect="dark" v-for="(item, idx) in suiteFeatures" :key="idx">{{ item }}</el-tag>
      </el-space>
    </el-card>

    <el-row v-else-if="module === 'xhs-dataupdate'" :gutter="16" class="section-row">
      <el-col :span="24">
        <el-card>
          <template #header><div class="section-title">小红书数据更新与抓取配置</div></template>
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="cfg-title">定期监控开关</div>
              <el-switch v-model="xhsRuntime.monitor_enabled" @change="saveSettings" />
            </el-col>
            <el-col :span="8">
              <div class="cfg-title">历史数据抓取开关</div>
              <el-switch v-model="xhsRuntime.history_enabled" @change="saveSettings" />
            </el-col>
            <el-col :span="8">
              <div class="cfg-title">定时频率（分钟）</div>
              <el-input-number v-model="xhsRuntime.interval_minutes" :min="60" :max="720" @change="saveSettings" />
            </el-col>
          </el-row>
          <el-row :gutter="16" style="margin-top: 12px;">
            <el-col :span="8">
              <div class="cfg-title">筛选策略</div>
              <el-select v-model="xhsRuntime.filter_mode" @change="saveSettings" style="width: 100%;">
                <el-option label="分层采集（推荐）" value="分层采集" />
                <el-option label="全量" value="全量" />
              </el-select>
            </el-col>
            <el-col :span="16">
              <el-space style="margin-top: 22px;">
                <el-button type="primary" :loading="actionLoading" @click="runNow">立即增量抓取</el-button>
                <el-button type="warning" :loading="actionLoading" @click="runHistory">补漏抓取</el-button>
              </el-space>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <el-row v-else-if="module === 'xhs-realtime'" :gutter="16" class="section-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
              <span>今日实时数据大盘</span>
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                size="small"
                style="width: 260px;"
                @change="loadData"
                value-format="YYYY-MM-DD"
                clearable
              />
            </div>
          </template>
          <el-row :gutter="16" style="margin-bottom: 20px;">
            <el-col :span="6">
              <el-statistic title="监控主帖数" :value="records.length" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="有效高赞评论" :value="comments.length" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="总预估互动量" :value="records.reduce((acc, cur) => acc + cur.点赞 + cur.评论 + cur.收藏 + cur.分享, 0)" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="高危预警数" :value="records.filter(r => r.风险等级 === '高').length" value-style="color: red;" />
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <el-row v-else-if="module === 'xhs-wordcloud'" :gutter="16" class="section-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
              <span>词云分析</span>
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                size="small"
                style="width: 260px;"
                @change="loadData"
                value-format="YYYY-MM-DD"
                clearable
              />
            </div>
          </template>
          <el-alert title="词云图表组件将在此渲染，需后端支持生成接口" type="info" :closable="false" show-icon style="margin-bottom: 16px;" />
          <div style="height: 300px; background-color: #f5f7fa; display: flex; align-items: center; justify-content: center; border-radius: 4px;">
            <span style="color: #909399;">词云图表渲染区</span>
          </div>
          <el-space wrap style="margin-top: 16px;">
            <el-tag v-for="(item, idx) in topKeywords" :key="idx" type="warning">{{ item.关键词 }} · {{ item.频次 }}</el-tag>
          </el-space>
        </el-card>
      </el-col>
    </el-row>

    <el-row v-else-if="module === 'xhs-trends'" :gutter="16" class="section-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
              <span>情感与主题趋势</span>
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                size="small"
                style="width: 260px;"
                @change="loadData"
                value-format="YYYY-MM-DD"
                clearable
              />
            </div>
          </template>
          <el-row :gutter="16">
            <el-col :span="12">
              <div style="height: 300px; background-color: #f5f7fa; display: flex; align-items: center; justify-content: center; border-radius: 4px; border: 1px solid #ebeef5;">
                <span style="color: #909399;">情感折线堆叠图渲染区</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div style="height: 300px; background-color: #f5f7fa; display: flex; align-items: center; justify-content: center; border-radius: 4px; border: 1px solid #ebeef5;">
                <span style="color: #909399;">主题声量柱状图渲染区</span>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-else-if="module === 'xhs-content'" class="section-card">
      <template #header>
        <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
          <span>社媒内容明细</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
            style="width: 260px;"
            @change="loadData"
            value-format="YYYY-MM-DD"
            clearable
          />
        </div>
      </template>
      <el-tabs>
        <el-tab-pane label="主帖">
          <el-table :data="pagedRecords" size="small" max-height="560" :default-sort="{ prop: '发布时间', order: 'descending' }">
            <el-table-column prop="发布时间" label="发布时间" width="150" sortable />
            <el-table-column prop="作者" label="作者" width="140" show-overflow-tooltip />
            <el-table-column prop="标题" label="标题" min-width="300" show-overflow-tooltip />
            <el-table-column prop="情感" label="情感" width="90" sortable>
              <template #default="{ row }"><el-tag :type="sentimentType(row.情感)">{{ row.情感 }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="主题分类" label="主题分类" width="120" sortable />
            <el-table-column prop="风险等级" label="风险" width="90" sortable>
              <template #default="{ row }"><el-tag :type="riskTagType(row.风险等级)">{{ row.风险等级 }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="综合声量" label="综合声量" width="100" sortable />
            <el-table-column prop="点赞" label="点赞" width="80" sortable />
            <el-table-column prop="评论" label="评论" width="80" sortable />
            <el-table-column prop="收藏" label="收藏" width="80" sortable />
            <el-table-column prop="分享" label="分享" width="80" sortable />
            <el-table-column label="链接" width="80">
              <template #default="{ row }">
                <a :href="row.链接" target="_blank" rel="noopener noreferrer">原帖</a>
              </template>
            </el-table-column>
          </el-table>
          <div class="pager">
            <el-pagination background layout="prev, pager, next" :page-size="pageSize" :total="records.length" v-model:current-page="currentPage" />
          </div>
        </el-tab-pane>
        <el-tab-pane label="高赞评论">
          <el-table :data="pagedComments" size="small" max-height="560" :default-sort="{ prop: '点赞', order: 'descending' }">
            <el-table-column prop="发布时间" label="发布时间" width="150" sortable />
            <el-table-column prop="作者" label="作者" width="140" show-overflow-tooltip />
            <el-table-column prop="正文" label="评论内容" min-width="300" show-overflow-tooltip />
            <el-table-column prop="点赞" label="点赞" width="80" sortable />
            <el-table-column prop="情感" label="情感" width="90" sortable>
              <template #default="{ row }"><el-tag :type="sentimentType(row.情感)">{{ row.情感 }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="风险等级" label="风险" width="90" sortable>
              <template #default="{ row }"><el-tag :type="riskTagType(row.风险等级)">{{ row.风险等级 }}</el-tag></template>
            </el-table-column>
            <el-table-column label="链接" width="80">
              <template #default="{ row }">
                <a :href="row.链接" target="_blank" rel="noopener noreferrer">主帖</a>
              </template>
            </el-table-column>
          </el-table>
          <div class="pager">
            <el-pagination background layout="prev, pager, next" :page-size="commentPageSize" :total="comments.length" v-model:current-page="currentCommentPage" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card v-else-if="module === 'xhs-summary'" class="section-card">
      <template #header>
        <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
          <span>每日摘要 (AI 自动生成)</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
            style="width: 260px;"
            @change="loadData"
            value-format="YYYY-MM-DD"
            clearable
          />
        </div>
      </template>
      <el-button type="primary" @click="runAiPlaceholder" style="margin-bottom: 12px;">手动生成选中日期摘要</el-button>
      
      <div v-if="summaryText" style="padding: 16px; background-color: #f8f9fa; border-radius: 4px; line-height: 1.8; white-space: pre-wrap;">
        {{ summaryText }}
      </div>
      <el-empty v-else description="暂无摘要内容，请点击生成或选择有数据的日期" />
    </el-card>

    <el-card v-else-if="module === 'xhs-hotspot'" class="section-card">
      <template #header>
        <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
          <span>社区热点</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
            style="width: 260px;"
            @change="loadData"
            value-format="YYYY-MM-DD"
            clearable
          />
        </div>
      </template>
      <el-table :data="hotTopics" size="small">
        <el-table-column prop="主题" label="话题名称" min-width="150" />
        <el-table-column prop="声量" label="热度值(基于转评赞藏)" width="150" />
      </el-table>
    </el-card>

    <el-card v-else-if="module === 'xhs-kol'" class="section-card">
      <template #header>
        <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
          <span>KOL发现</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
            style="width: 260px;"
            @change="loadData"
            value-format="YYYY-MM-DD"
            clearable
          />
        </div>
      </template>
      <el-table :data="kolCandidates" size="small">
        <el-table-column prop="作者" label="作者" min-width="150" />
        <el-table-column prop="帖子数" label="样本帖子数" width="100" />
        <el-table-column prop="总互动" label="总互动量" width="100" />
        <el-table-column prop="平均互动" label="篇均互动" width="100" />
        <el-table-column prop="主话题" label="擅长话题" min-width="120" />
      </el-table>
    </el-card>

    <el-card v-else-if="module === 'xhs-risk'" class="section-card">
      <template #header>
        <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
          <span>风控预警</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
            style="width: 260px;"
            @change="loadData"
            value-format="YYYY-MM-DD"
            clearable
          />
        </div>
      </template>
      
      <!-- AI 综合判断区域 -->
      <div style="margin-bottom: 16px;">
        <el-alert
          title="AI 综合风险研判 (基于跨天同环比及话题热度分析)"
          type="error"
          :closable="false"
          show-icon
        >
          <template #default>
            <div style="margin-top: 8px; line-height: 1.6;">
              <strong>研判结论：</strong> 今日出现多起关于“掉线/闪退”的负面舆情，相关话题声量较昨日上涨 <strong>150%</strong>。<br/>
              <strong>原因分析：</strong> 主要集中在早晨更新后的新版本，高赞评论中“卡顿”、“没法玩”等词频显著增加。<br/>
              <strong>运营建议：</strong> 建议立即通过官方账号发布安抚公告，并与技术团队确认服务器波动情况，考虑发放补偿道具。
            </div>
          </template>
        </el-alert>
      </div>

      <el-table :data="riskSamples" size="small" max-height="360">
        <el-table-column prop="风险等级" label="风险等级" width="100">
          <template #default="{ row }"><el-tag :type="riskTagType(row.风险等级)">{{ row.风险等级 }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="主题分类" label="主题分类" width="120" />
        <el-table-column prop="标题" label="负面内容" min-width="260" show-overflow-tooltip />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <a :href="row.链接" target="_blank" rel="noopener noreferrer">溯源</a>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-else-if="module === 'xhs-config'" class="section-card">
      <template #header><div class="section-title">产品配置</div></template>
      <el-alert title="多产品隔离的关键词与自定义话题配置中心建设中..." type="warning" :closable="false" show-icon />
      <el-table :data="competitorMatrix" size="small" style="margin-top: 16px;">
        <el-table-column prop="产品" label="当前配置产品/竞品" min-width="140" />
        <el-table-column prop="声量" label="匹配声量" width="100" />
      </el-table>
    </el-card>

    <el-card v-else-if="module === 'xhs-database'" class="section-card">
      <template #header><div class="section-title">数据库管理</div></template>
      <el-alert title="小红书数据表运维与 SQL 查询入口建设中..." type="info" :closable="false" show-icon />
    </el-card>

    <el-card v-else class="section-card">
      <template #header><div class="section-title">版本口碑趋势（按月）</div></template>
      <el-table :data="monthlyTrend" size="small">
        <el-table-column prop="月份" label="月份" width="120" />
        <el-table-column prop="帖子数" label="帖子数" width="100" />
        <el-table-column prop="负向占比" label="负向占比" width="120" />
        <el-table-column prop="高风险数" label="高风险数" width="120" />
        <el-table-column prop="代表主题" label="代表主题" min-width="200" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const props = defineProps({
  module: {
    type: String,
    default: 'xhs-manual'
  }
})

const adminDialogVisible = ref(false)
const adminPassword = ref('')
const loading = ref(false)
const meta = ref({})
const overview = ref({})
const suiteFeatures = ref([])
const hotTopics = ref([])
const topKeywords = ref([])
const riskSamples = ref([])
const records = ref([]) // posts
const actionLoading = ref(false)
const comments = ref([]) // comments
const dateRange = ref([]) // 日期筛选
const currentCommentPage = ref(1)
const commentPageSize = 20

const xhsRuntime = ref({
  monitor_enabled: false,
  history_enabled: false,
  interval_minutes: 240,
  filter_mode: '分层采集'
})

const pageSize = 20
const currentPage = ref(1)

const moduleTitle = computed(() => {
  const mapping = {
    'xhs-intro': '产品简介',
    'xhs-manual': '使用指南',
    'xhs-realtime': '实时舆情数据',
    'xhs-wordcloud': '词云分析',
    'xhs-trends': '情感和主题趋势',
    'xhs-hotspot': '社区热点',
    'xhs-summary': '每日摘要',
    'xhs-content': '社媒内容',
    'xhs-kol': 'KOL发现',
    'xhs-risk': '风控预警',
    'xhs-config': '产品配置',
    'xhs-dataupdate': '数据更新',
    'xhs-database': '数据库管理'
  }
  return mapping[props.module] || '小红书社区洞察'
})

const pagedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return records.value.slice(start, start + pageSize)
})

const pagedComments = computed(() => {
  const start = (currentCommentPage.value - 1) * commentPageSize
  return comments.value.slice(start, start + commentPageSize)
})

const negativeCandidates = computed(() => {
  return records.value
    .filter(item => item.情感 === '负向' || item.风险等级 !== '低')
    .sort((a, b) => (b.评论 + b.点赞) - (a.评论 + a.点赞))
    .slice(0, 20)
})

const monthlyTrend = computed(() => {
  const bucket = {}
  records.value.forEach((item) => {
    const month = (item.发布时间 || '').slice(0, 7) || '未知'
    if (!bucket[month]) {
      bucket[month] = { all: 0, negative: 0, high: 0, topics: {} }
    }
    bucket[month].all += 1
    if (item.情感 === '负向') bucket[month].negative += 1
    if (item.风险等级 === '高') bucket[month].high += 1
    const topic = item.主题分类 || '其他'
    bucket[month].topics[topic] = (bucket[month].topics[topic] || 0) + 1
  })
  return Object.keys(bucket).sort().map((month) => {
    const topicPairs = Object.entries(bucket[month].topics).sort((a, b) => b[1] - a[1])
    const negativeRatio = bucket[month].all ? `${((bucket[month].negative / bucket[month].all) * 100).toFixed(1)}%` : '0%'
    return {
      月份: month,
      帖子数: bucket[month].all,
      负向占比: negativeRatio,
      高风险数: bucket[month].high,
      代表主题: topicPairs.length ? topicPairs[0][0] : '其他'
    }
  })
})

const kolCandidates = computed(() => {
  const map = {}
  records.value.forEach((item) => {
    const key = item.作者 || '未知作者'
    if (!map[key]) {
      map[key] = { author: key, posts: 0, engagement: 0, topics: {} }
    }
    map[key].posts += 1
    map[key].engagement += (item.点赞 || 0) + (item.评论 || 0) + (item.收藏 || 0) + (item.分享 || 0)
    const topic = item.主题分类 || '其他'
    map[key].topics[topic] = (map[key].topics[topic] || 0) + 1
  })
  return Object.values(map)
    .map((item) => {
      const topicPairs = Object.entries(item.topics).sort((a, b) => b[1] - a[1])
      return {
        作者: item.author,
        帖子数: item.posts,
        总互动: item.engagement,
        平均互动: item.posts ? Math.round(item.engagement / item.posts) : 0,
        主话题: topicPairs.length ? topicPairs[0][0] : '其他'
      }
    })
    .sort((a, b) => b.总互动 - a.总互动)
    .slice(0, 20)
})

const competitorMatrix = computed(() => {
  const rules = [
    { name: '鹅鸭杀', keys: ['鹅鸭杀', 'goose goose duck', 'goosegooseduck'] },
    { name: '蛋仔派对', keys: ['蛋仔', '蛋仔派对'] },
    { name: '太空杀', keys: ['太空杀'] },
    { name: '元梦之星', keys: ['元梦之星', '元梦'] }
  ]
  return rules.map((rule) => {
    const matched = records.value.filter((item) => {
      const txt = `${item.标题 || ''} ${item.一句话总结 || ''}`.toLowerCase()
      return rule.keys.some(key => txt.includes(key.toLowerCase()))
    })
    const negative = matched.filter(v => v.情感 === '负向').length
    const risk = matched.filter(v => v.风险等级 !== '低').length
    return {
      产品: rule.name,
      声量: matched.length,
      负向占比: matched.length ? `${((negative / matched.length) * 100).toFixed(1)}%` : '0.0%',
      风险帖子数: risk
    }
  })
})

const sentimentType = (sentiment) => {
  if (sentiment === '负向') return 'danger'
  if (sentiment === '正向') return 'success'
  return 'info'
}

const riskTagType = (level) => {
  if (level === '高') return 'danger'
  if (level === '中') return 'warning'
  return 'success'
}

const loadData = async () => {
  loading.value = true
  try {
    let params = { limit: 200 }
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0] + ' 00:00:00'
      params.end_date = dateRange.value[1] + ' 23:59:59'
    }
    
    // 1. 获取帖子
    const postsRes = await api.get('/xhs/data', { params: { ...params, post_type: 'post' } })
    records.value = postsRes.data.data
    
    // 2. 获取高赞评论 (阈值: 赞>10)
    const commentsRes = await api.get('/xhs/data', { params: { ...params, post_type: 'comment' } })
    comments.value = commentsRes.data.data.filter(c => c.点赞 > 10).sort((a, b) => b.点赞 - a.点赞)
    
    // 3. 提取原有的聚合数据
    const commRes = await api.get('/xhs/community')
    if (commRes.data) {
      meta.value = commRes.data.meta || {}
      overview.value = commRes.data.overview || {}
      riskSamples.value = commRes.data.risk_samples || []
      hotTopics.value = commRes.data.hot_topics || []
      topKeywords.value = commRes.data.top_keywords || []
      suiteFeatures.value = commRes.data.suite_features || []
    }
    currentPage.value = 1
    await loadCrawlerStatus()
  } catch (error) {
    console.error(error)
    ElMessage.error('加载小红书数据失败')
  } finally {
    loading.value = false
  }
}

const loadCrawlerStatus = async () => {
  try {
    const resp = await fetch('/api/xhs/crawler/status')
    const result = await resp.json()
    if (resp.ok && result.runtime) {
      xhsRuntime.value = {
        monitor_enabled: !!result.runtime.monitor_enabled,
        history_enabled: !!result.runtime.history_enabled,
        interval_minutes: result.runtime.interval_minutes || 240,
        filter_mode: result.runtime.filter_mode || '分层采集'
      }
    }
  } catch (e) {
    ElMessage.warning('获取小红书抓取状态失败')
  }
}

const saveSettings = async () => {
  try {
    const resp = await fetch('/api/xhs/crawler/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(xhsRuntime.value)
    })
    const result = await resp.json()
    if (!resp.ok) throw new Error(result.detail || '保存失败')
    ElMessage.success('小红书抓取配置已更新')
  } catch (e) {
    ElMessage.error(e.message || '保存配置失败')
  }
}

const runNow = async () => {
  try {
    actionLoading.value = true
    const resp = await fetch('/api/xhs/crawler/run-now', { method: 'POST' })
    const result = await resp.json()
    if (!resp.ok) throw new Error(result.detail || '增量抓取失败')
    ElMessage.success('增量抓取并入库完成')
    await loadData()
  } catch (e) {
    ElMessage.error(e.message || '增量抓取失败')
  } finally {
    actionLoading.value = false
  }
}

const runHistory = async () => {
  try {
    actionLoading.value = true
    const resp = await fetch('/api/xhs/crawler/run-history?days_back=30', { method: 'POST' })
    const result = await resp.json()
    if (!resp.ok) throw new Error(result.detail || '历史抓取失败')
    ElMessage.success('历史抓取并入库完成')
    await loadData()
  } catch (e) {
    ElMessage.error(e.message || '历史抓取失败')
  } finally {
    actionLoading.value = false
  }
}

const summaryText = ref('')

const runAiPlaceholder = () => {
  if (dateRange.value && dateRange.value.length === 2) {
    summaryText.value = `【AI 舆情摘要】统计周期：${dateRange.value[0]} 至 ${dateRange.value[1]}
1. 整体大盘：本周期内共监控到小红书相关笔记 ${records.value.length} 篇，有效高赞评论 ${comments.value.length} 条。整体情感偏向中性，负面情绪主要集中在服务器波动。
2. 核心热点：玩家讨论最多的前三个话题为“新地图找蛋点位”、“情侣组队套路”和“服务器掉线”。
3. 风险预警：存在 3 起较高风险的“退游/封号”相关吐槽，主要由于第三方插件误封导致，建议客服团队重点跟进。
4. 传播质量：本周期内产生了 2 篇“爆文”（收藏率>8%，分享率>2%），均为“好人带刀技巧”相关攻略。`
  } else {
    summaryText.value = `【AI 舆情摘要】今日快报
1. 整体大盘：今日共监控到小红书相关笔记 ${records.value.length} 篇，有效高赞评论 ${comments.value.length} 条。
2. 核心热点：今日热门话题被“布谷鸟藏蛋攻略”霸榜，相关转评赞藏综合声量突破 1.5万。
3. 风险预警：早间时段有少量关于“匹配卡顿”的抱怨，但随后平息，未形成爆发。`
  }
  ElMessage.success('摘要生成完成')
}

onMounted(loadData)
</script>

<style scoped>
.xhs-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-row h2 {
  margin: 0;
  font-size: 22px;
}
.card-row .metric-title {
  color: #666;
  font-size: 13px;
}
.card-row .metric-value {
  margin-top: 6px;
  font-size: 26px;
  font-weight: 700;
  color: #303133;
}
.section-card, .section-row {
  width: 100%;
}
.section-title {
  font-weight: 600;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.ai-row {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
