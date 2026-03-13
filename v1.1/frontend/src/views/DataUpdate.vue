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
          <el-statistic title="最新评价日期" :value="status.last_crawl_date || '无数据'" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="缺失天数" :value="status.gap_days || 0" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="最后爬取状态" :value="status.last_crawl_status || '无记录'" />
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
          <el-select v-model="form.product" placeholder="请选择产品" style="width: 200px">
            <el-option
              v-for="product in products"
              :key="product.name"
              :label="product.name"
              :value="product.name"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="选择平台">
          <el-select v-model="form.platform" placeholder="请选择平台" style="width: 200px">
            <el-option label="TapTap" value="TapTap" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="爬取数量">
          <el-input-number v-model="form.maxReviews" :min="100" :max="10000" :step="500" />
          <span class="form-tip">仅全量爬取时生效</span>
        </el-form-item>
        
        <el-form-item>
          <el-space wrap>
            <el-button type="primary" @click="crawlFull" :loading="crawling">
              全量爬取
            </el-button>
            <el-button type="success" @click="crawlIncremental" :loading="crawling">
              增量更新
            </el-button>
            <el-button type="warning" @click="fillGaps" :loading="crawling">
              自动补漏
            </el-button>
          </el-space>
        </el-form-item>
      </el-form>
      
      <el-divider />
      
      <div class="mode-description">
        <h4>模式说明</h4>
        <ul>
          <li><strong>全量爬取</strong>：一次性爬取所有历史数据，适合首次爬取或重新爬取</li>
          <li><strong>增量更新</strong>：从最后爬取日期开始，继续爬到今天，适合定期更新</li>
          <li><strong>自动补漏</strong>：检测最近30天内缺失的日期，自动补齐数据</li>
        </ul>
      </div>
    </el-card>

    <el-card class="log-card">
      <template #header>
        <span>爬取日志</span>
      </template>
      
      <el-table :data="logs" style="width: 100%">
        <el-table-column prop="start_time" label="开始时间" width="180" />
        <el-table-column prop="end_time" label="结束时间" width="180" />
        <el-table-column prop="spider_name" label="爬取模式" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reviews_added" label="新增" width="80" />
        <el-table-column prop="reviews_updated" label="更新" width="80" />
        <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const loading = ref(false)
const crawling = ref(false)

const status = ref({})
const logs = ref([])
const products = ref([])

const form = ref({
  product: '鹅鸭杀',
  platform: 'TapTap',
  maxReviews: 8000
})

const refreshStatus = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/api/crawler/status`, {
      params: {
        product_name: form.value.product,
        platform_name: form.value.platform
      }
    })
    status.value = res.data
  } catch (error) {
    ElMessage.error('获取状态失败：' + error.message)
  } finally {
    loading.value = false
  }
}

const getProducts = async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/crawler/products`)
    products.value = res.data.products
  } catch (error) {
    console.error('获取产品列表失败：', error)
  }
}

const crawlFull = async () => {
  crawling.value = true
  try {
    const res = await axios.post(`${API_BASE}/api/crawler/full`, null, {
      params: {
        product_name: form.value.product,
        platform_name: form.value.platform,
        max_reviews: form.value.maxReviews
      }
    })
    ElMessage.success(res.data.message)
    setTimeout(refreshStatus, 2000)
  } catch (error) {
    ElMessage.error('启动爬取失败：' + error.message)
  } finally {
    crawling.value = false
  }
}

const crawlIncremental = async () => {
  crawling.value = true
  try {
    const res = await axios.post(`${API_BASE}/api/crawler/incremental`, null, {
      params: {
        product_name: form.value.product,
        platform_name: form.value.platform
      }
    })
    ElMessage.success(res.data.message)
    setTimeout(refreshStatus, 2000)
  } catch (error) {
    ElMessage.error('启动爬取失败：' + error.message)
  } finally {
    crawling.value = false
  }
}

const fillGaps = async () => {
  crawling.value = true
  try {
    const res = await axios.post(`${API_BASE}/api/crawler/fill-gaps`, null, {
      params: {
        product_name: form.value.product,
        platform_name: form.value.platform
      }
    })
    if (res.data.status === 'skipped') {
      ElMessage.info(res.data.message)
    } else {
      ElMessage.success(res.data.message)
    }
    setTimeout(refreshStatus, 2000)
  } catch (error) {
    ElMessage.error('启动补漏失败：' + error.message)
  } finally {
    crawling.value = false
  }
}

onMounted(() => {
  getProducts()
  refreshStatus()
})
</script>

<style scoped>
.data-update {
  padding: 20px;
}

.status-card, .control-card, .log-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
</style>
