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
          <el-button v-if="!isAdmin" type="warning" size="small" @click="adminDialogVisible = true">管理员登录</el-button>
          <el-dropdown v-else @command="handleAdminCommand">
            <el-button type="primary" size="small">
              管理员选项<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="manual">使用指南</el-dropdown-item>
                <el-dropdown-item command="intro">产品简介</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
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
              <el-menu-item index="monitor">
                <el-icon><Monitor /></el-icon>
                <span>系统监控</span>
              </el-menu-item>
              <el-menu-item index="database">
                <el-icon><Grid /></el-icon>
                <span>数据库管理</span>
              </el-menu-item>
              <el-menu-item index="products">
                <el-icon><Setting /></el-icon>
                <span>产品管理</span>
              </el-menu-item>
            </el-sub-menu>
            
            <el-sub-menu index="xiaohongshu">
              <template #title>
                <el-icon><PictureFilled /></el-icon>
                <span>小红书监控</span>
              </template>
              <el-menu-item index="xhs-realtime">
                <el-icon><TrendCharts /></el-icon>
                <span>实时舆情数据</span>
              </el-menu-item>
              <el-menu-item index="xhs-wordcloud">
                <el-icon><Cloudy /></el-icon>
                <span>词云分析</span>
              </el-menu-item>
              <el-menu-item index="xhs-trends">
                <el-icon><DataAnalysis /></el-icon>
                <span>情感和主题趋势</span>
              </el-menu-item>
              <el-menu-item index="xhs-hotspot">
                <el-icon><Odometer /></el-icon>
                <span>社区热点</span>
              </el-menu-item>
              <el-menu-item index="xhs-summary">
                <el-icon><Document /></el-icon>
                <span>每日摘要</span>
              </el-menu-item>
              <el-menu-item index="xhs-content">
                <el-icon><Notebook /></el-icon>
                <span>社媒内容</span>
              </el-menu-item>
              <el-menu-item index="xhs-kol">
                <el-icon><User /></el-icon>
                <span>KOL发现</span>
              </el-menu-item>
              <el-menu-item index="xhs-risk">
                <el-icon><Warning /></el-icon>
                <span>风控预警</span>
              </el-menu-item>
              <el-menu-item index="xhs-config">
                <el-icon><Setting /></el-icon>
                <span>产品配置</span>
              </el-menu-item>
              <el-menu-item index="xhs-dataupdate">
                <el-icon><Refresh /></el-icon>
                <span>数据更新</span>
              </el-menu-item>
              <el-menu-item index="xhs-database">
                <el-icon><Grid /></el-icon>
                <span>数据库管理</span>
              </el-menu-item>
            </el-sub-menu>
          </el-menu>
        </el-aside>
        
        <el-main class="main-content">
          <RealtimeData v-if="activeMenu === 'realtime'" :data="data" @refresh="loadData" />
          <NegativeMonitor v-else-if="activeMenu === 'negative'" :data="data" />
          <WordCloud v-else-if="activeMenu === 'wordcloud'" :data="data" />
          <Reviews v-else-if="activeMenu === 'reviews'" :data="data" @refresh="loadData" />
          <AnalysisReport v-else-if="activeMenu === 'report'" :data="data" />
          <AlertSettings v-else-if="activeMenu === 'alert'" :data="data" @alert-change="handleAlertChange" />
          <DataUpdate v-else-if="activeMenu === 'dataupdate' && isAdmin" @refresh="loadData" />
          <SystemMonitor v-else-if="activeMenu === 'monitor' && isAdmin" />
          <DatabaseManage v-else-if="activeMenu === 'database' && isAdmin" />
          <el-result
            v-else-if="['dataupdate','monitor','database'].includes(activeMenu)"
            icon="warning"
            title="需要管理员登录"
            sub-title="数据更新、系统监控、数据库管理仅管理员可操作"
          >
            <template #extra>
              <el-button type="primary" @click="adminDialogVisible = true">立即登录</el-button>
            </template>
          </el-result>
          <ProductManage v-else-if="activeMenu === 'products'" @product-change="handleProductChange" />
          <XhsCommunity v-else-if="activeMenu.startsWith('xhs-')" :module="activeMenu" />
        </el-main>
      </el-container>
    </el-container>

    <el-dialog v-model="adminDialogVisible" title="管理员登录" width="420px">
      <el-input
        v-model="adminPassword"
        type="password"
        show-password
        placeholder="请输入管理员密码"
        @keyup.enter="loginAdmin"
      />
      <template #footer>
        <el-button @click="adminDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="adminLoading" @click="loginAdmin">登录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { 
  DataAnalysis, Monitor, Odometer, TrendCharts, Warning, 
  Cloudy, Document, Bell, PictureFilled, Notebook, Refresh, Setting, Grid, ArrowDown, User
} from '@element-plus/icons-vue'
import RealtimeData from './views/RealtimeData.vue'
import NegativeMonitor from './views/NegativeMonitor.vue'
import WordCloud from './views/WordCloud.vue'
import Reviews from './views/Reviews.vue'
import AnalysisReport from './views/AnalysisReport.vue'
import AlertSettings from './views/AlertSettings.vue'
import DataUpdate from './views/DataUpdate.vue'
import SystemMonitor from './views/SystemMonitor.vue'
import ProductManage from './views/ProductManage.vue'
import DatabaseManage from './views/DatabaseManage.vue'
import XhsCommunity from './views/XhsCommunity.vue'
import { ElMessage } from 'element-plus'
import api from './api'

const activeMenu = ref('realtime')
const selectedProduct = ref(null)
const products = ref([])
const updateTime = ref('')
const data = ref(null)
const alertRules = ref([])
const isAdmin = ref(false)
const adminDialogVisible = ref(false)
const adminPassword = ref('')
const adminLoading = ref(false)
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

const handleProductChange = () => {
  loadProducts()
}

const loginAdmin = async () => {
  if (!adminPassword.value) {
    ElMessage.warning('请输入管理员密码')
    return
  }
  adminLoading.value = true
  try {
    const res = await api.post('/admin/login', { password: adminPassword.value })
    localStorage.setItem('adminToken', res.data.token)
    isAdmin.value = true
    adminDialogVisible.value = false
    adminPassword.value = ''
    ElMessage.success('管理员登录成功')
  } catch (error) {
    ElMessage.error('登录失败：' + (error.response?.data?.detail || error.message))
  } finally {
    adminLoading.value = false
  }
}

const checkAdmin = async () => {
  try {
    const res = await api.get('/admin/status')
    isAdmin.value = !!res.data.logged_in
  } catch {
    isAdmin.value = false
  }
}

const handleAdminCommand = (command) => {
  if (command === 'logout') {
    logoutAdmin()
  } else if (command === 'manual') {
    activeMenu.value = 'xhs-manual' // 或展示弹窗/跳转新页面
    ElMessage.info('正在打开使用指南')
  } else if (command === 'intro') {
    activeMenu.value = 'xhs-intro'
    ElMessage.info('正在打开产品简介')
  }
}

const logoutAdmin = async () => {
  try {
    await api.post('/admin/logout')
  } catch {}
  localStorage.removeItem('adminToken')
  isAdmin.value = false
  ElMessage.success('已退出管理员')
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
    products.value = [{ id: 1, name: '鹅鸭杀', code: 'goose_goose_duck' }]
    selectedProduct.value = 1
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
  await checkAdmin()
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
