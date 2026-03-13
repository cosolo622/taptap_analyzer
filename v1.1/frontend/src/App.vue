<template>
  <div class="app-container">
    <el-container>
      <el-header class="header">
        <div class="logo">
          <el-icon size="24"><DataAnalysis /></el-icon>
          <span>数据中心产品舆情监控</span>
        </div>
        <div class="header-right">
          <el-select v-model="selectedProduct" placeholder="选择产品" style="width: 180px" @change="loadData">
            <el-option v-for="product in products" :key="product.id" :label="product.name" :value="product.id" />
          </el-select>
          <span class="update-time">更新时间: {{ updateTime }}</span>
          <el-badge :value="alertCount" :hidden="alertCount === 0" class="alert-badge">
            <el-button :icon="Bell" circle @click="handleAlertClick" />
          </el-badge>
        </div>
      </el-header>
      
      <el-container>
        <el-aside width="220px" class="sidebar">
          <el-menu 
            :default-active="activeMenu" 
            :default-openeds="['taptap']"
            @select="handleMenuSelect"
          >
            <el-sub-menu index="taptap">
              <template #title>
                <el-icon><Monitor /></el-icon>
                <span>TapTap监控</span>
                <el-badge v-if="hasAlert" is-dot class="menu-alert-dot" />
              </template>
              <el-menu-item index="realtime">
                <el-icon><Odometer /></el-icon>
                <span>实时舆情数据</span>
              </el-menu-item>
              <el-menu-item index="negative">
                <el-icon><Warning /></el-icon>
                <span>负面舆情监控</span>
              </el-menu-item>
              <el-menu-item index="wordcloud">
                <el-icon><Cloudy /></el-icon>
                <span>词云分析</span>
              </el-menu-item>
              <el-menu-item index="reviews">
                <el-icon><Document /></el-icon>
                <span>评价明细</span>
              </el-menu-item>
              <el-menu-item index="report">
                <el-icon><Notebook /></el-icon>
                <span>舆情分析报告</span>
              </el-menu-item>
              <el-menu-item index="alert">
                <el-icon><Bell /></el-icon>
                <span>预警设置</span>
                <el-badge v-if="hasAlert" is-dot class="submenu-alert-dot" />
              </el-menu-item>
              <el-menu-item index="dataupdate">
                <el-icon><Refresh /></el-icon>
                <span>数据更新</span>
              </el-menu-item>
            </el-sub-menu>
            
            <el-sub-menu index="xiaohongshu" disabled>
              <template #title>
                <el-icon><PictureFilled /></el-icon>
                <span>小红书监控</span>
              </template>
              <el-menu-item index="xhs-placeholder" disabled>
                <span style="color: #909399;">开发中...</span>
              </el-menu-item>
            </el-sub-menu>
          </el-menu>
        </el-aside>
        
        <el-main class="main-content">
          <RealtimeData v-if="activeMenu === 'realtime'" :data="data" @refresh="loadData" />
          <NegativeMonitor v-else-if="activeMenu === 'negative'" :data="data" />
          <WordCloud v-else-if="activeMenu === 'wordcloud'" :data="data" />
          <Reviews v-else-if="activeMenu === 'reviews'" :data="data" />
          <AnalysisReport v-else-if="activeMenu === 'report'" :data="data" />
          <AlertSettings v-else-if="activeMenu === 'alert'" :data="data" @alert-change="handleAlertChange" />
          <DataUpdate v-else-if="activeMenu === 'dataupdate'" @refresh="loadData" />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { 
  DataAnalysis, Monitor, Odometer, TrendCharts, Warning, 
  Cloudy, Document, Bell, PictureFilled, Notebook, Refresh
} from '@element-plus/icons-vue'
import RealtimeData from './views/RealtimeData.vue'
import NegativeMonitor from './views/NegativeMonitor.vue'
import WordCloud from './views/WordCloud.vue'
import Reviews from './views/Reviews.vue'
import AnalysisReport from './views/AnalysisReport.vue'
import AlertSettings from './views/AlertSettings.vue'
import DataUpdate from './views/DataUpdate.vue'

const activeMenu = ref('realtime')
const selectedProduct = ref(1)
const products = ref([{ id: 1, name: '鹅鸭杀', code: 'goose_goose_duck' }])
const updateTime = ref('')
const data = ref(null)
const alertRules = ref([])
const hasAlert = computed(() => alertRules.value.some(rule => rule.triggered))
const alertCount = computed(() => alertRules.value.filter(rule => rule.triggered).length)

const handleMenuSelect = (index) => {
  activeMenu.value = index
}

const handleAlertClick = () => {
  activeMenu.value = 'alert'
}

const handleAlertChange = (rules) => {
  alertRules.value = rules
}

const loadProducts = async () => {
  try {
    const response = await fetch('/api/products')
    const result = await response.json()
    if (result.products && result.products.length > 0) {
      products.value = result.products
      if (!selectedProduct.value) {
        selectedProduct.value = result.products[0].id
      }
    }
  } catch (error) {
    console.error('加载产品列表失败:', error)
  }
}

const loadData = async () => {
  try {
    let url = '/api/data?use_db=true'
    if (selectedProduct.value) {
      url += `&product_id=${selectedProduct.value}`
    }
    
    const response = await fetch(url)
    const result = await response.json()
    data.value = result
    updateTime.value = new Date().toLocaleString('zh-CN')
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

const loadAlertRules = () => {
  const saved = localStorage.getItem('alertRules')
  if (saved) {
    alertRules.value = JSON.parse(saved)
  }
}

onMounted(async () => {
  await loadProducts()
  await loadData()
  loadAlertRules()
})
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: bold;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.update-time {
  font-size: 14px;
  opacity: 0.8;
}

.alert-badge {
  margin-left: 10px;
}

.sidebar {
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
}

.main-content {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

.menu-alert-dot {
  margin-left: 8px;
}

.submenu-alert-dot {
  margin-left: auto;
}

:deep(.el-sub-menu__title) {
  display: flex;
  align-items: center;
}

:deep(.el-menu-item) {
  display: flex;
  align-items: center;
}
</style>
