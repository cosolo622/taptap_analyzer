<template>
  <div class="product-manage">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>产品管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加产品
          </el-button>
        </div>
      </template>
      
      <el-table :data="products" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="产品名称" width="150" />
        <el-table-column prop="code" label="产品代码" width="150" />
        <el-table-column prop="platform" label="平台" width="100">
          <template #default>
            <el-tag size="small">TapTap</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '监控中' : '已暂停' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="review_count" label="评价数" width="100" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="testCrawl(row)">
              测试爬取
            </el-button>
            <el-button size="small" type="warning" @click="pauseProduct(row)">
              {{ row.status === 'active' ? '暂停' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <span>添加产品流程说明</span>
      </template>
      
      <el-steps :active="1" simple>
        <el-step title="搜索产品" description="输入产品名称，模糊匹配TapTap游戏" />
        <el-step title="确认信息" description="选择正确的游戏，确认产品代码" />
        <el-step title="测试爬取" description="爬取少量数据验证配置正确" />
        <el-step title="正式监控" description="测试通过后，产品自动加入监控" />
      </el-steps>
      
      <el-alert type="info" :closable="false" style="margin-top: 15px;">
        <template #title>
          <span>添加新产品后，建议先进行测试爬取（爬取3-5条数据），确认爬虫能正常工作后再正式启用监控。</span>
        </template>
      </el-alert>
    </el-card>

    <el-dialog v-model="addDialogVisible" title="添加监控产品" width="600px">
      <el-form :model="productForm" label-width="100px">
        <el-form-item label="产品名称">
          <el-input 
            v-model="productForm.name" 
            placeholder="输入产品名称（支持模糊匹配）" 
            @input="debounceSearch"
          />
        </el-form-item>
        
        <div v-if="searching" class="search-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>搜索中...</span>
        </div>
        
        <div v-else-if="searchResults.length > 0" class="search-results">
          <div class="search-tip">找到 {{ searchResults.length }} 个匹配结果，请选择：</div>
          <el-radio-group v-model="selectedProduct" class="search-radio-group">
            <el-radio 
              v-for="item in searchResults" 
              :key="item.id" 
              :label="item"
              class="search-radio-item"
            >
              <div class="search-item">
                <span class="search-item-name">{{ item.name }}</span>
                <span class="search-item-info">{{ item.platform }} | 评分: {{ item.rating || '-' }}</span>
              </div>
            </el-radio>
          </el-radio-group>
        </div>
        
        <div v-else-if="productForm.name && !searching && searchResults.length === 0" class="search-empty">
          <el-empty description="未找到匹配的产品" :image-size="60" />
        </div>
        
        <el-form-item label="产品代码" v-if="selectedProduct">
          <el-input v-model="productForm.code" placeholder="产品唯一标识（自动生成）" disabled />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addProduct" :disabled="!selectedProduct">
          确认添加
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="testDialogVisible" title="测试爬取" width="500px">
      <el-form :model="testForm" label-width="100px">
        <el-form-item label="产品名称">
          <el-input :value="testForm.productName" disabled />
        </el-form-item>
        <el-form-item label="爬取数量">
          <el-input-number v-model="testForm.count" :min="3" :max="20" />
          <span class="form-tip">建议3-5条验证配置</span>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="testDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="runTestCrawl" :loading="testCrawling">
          开始测试
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Loading } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['product-change'])

const products = ref([])

const addDialogVisible = ref(false)
const productForm = ref({
  name: '',
  platform: 'taptap',
  code: ''
})
const searchResults = ref([])
const selectedProduct = ref(null)
const searching = ref(false)

const testDialogVisible = ref(false)
const testForm = ref({
  productId: null,
  productName: '',
  count: 5
})
const testCrawling = ref(false)

let searchTimer = null

const debounceSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  
  if (!productForm.value.name) {
    searchResults.value = []
    selectedProduct.value = null
    return
  }
  
  searching.value = true
  searchTimer = setTimeout(() => {
    searchProduct()
  }, 500)
}

const searchProduct = async () => {
  try {
    const response = await axios.get('/api/products/search', {
      params: { keyword: productForm.value.name }
    })
    searchResults.value = response.data.results || []
    
    if (searchResults.value.length === 1) {
      selectedProduct.value = searchResults.value[0]
      productForm.value.code = selectedProduct.value.id
    }
  } catch (error) {
    console.error('搜索产品失败:', error)
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

const showAddDialog = () => {
  productForm.value = { name: '', platform: 'taptap', code: '' }
  searchResults.value = []
  selectedProduct.value = null
  addDialogVisible.value = true
}

const addProduct = async () => {
  if (!selectedProduct.value) {
    ElMessage.warning('请选择一个产品')
    return
  }
  
  try {
    const response = await axios.post('/api/products', null, {
      params: {
        name: selectedProduct.value.name,
        platform: 'taptap',
        code: selectedProduct.value.id
      }
    })
    
    ElMessage.success('添加成功，建议进行测试爬取验证')
    addDialogVisible.value = false
    loadProducts()
    emit('product-change')
  } catch (error) {
    ElMessage.error('添加失败: ' + (error.response?.data?.detail || error.message))
  }
}

const pauseProduct = async (row) => {
  try {
    await axios.post(`/api/products/${row.id}/pause`)
    ElMessage.success(row.status === 'active' ? '已暂停监控' : '已启用监控')
    loadProducts()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const testCrawl = (row) => {
  testForm.value = {
    productId: row.id,
    productName: row.name,
    count: 5
  }
  testDialogVisible.value = true
}

const runTestCrawl = async () => {
  testCrawling.value = true
  try {
    const response = await axios.post('/api/crawler/start', null, {
      params: {
        product_id: testForm.value.productId,
        max_count: testForm.value.count
      }
    })
    
    ElMessage.success('测试爬取已启动，请到系统监控查看进度')
    testDialogVisible.value = false
  } catch (error) {
    ElMessage.error('启动失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    testCrawling.value = false
  }
}

const loadProducts = async () => {
  try {
    const response = await axios.get('/api/products')
    products.value = response.data.products || []
  } catch (error) {
    console.error('加载产品列表失败:', error)
  }
}

onMounted(() => {
  loadProducts()
})
</script>

<style scoped>
.product-manage {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  color: #909399;
}

.search-results {
  margin-top: 10px;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
}

.search-tip {
  font-size: 12px;
  color: #909399;
  margin-bottom: 10px;
}

.search-radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.search-radio-item {
  display: flex;
  width: 100%;
  padding: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  margin: 0;
}

.search-radio-item:hover {
  background: #f5f7fa;
}

.search-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.search-item-name {
  font-weight: 500;
}

.search-item-info {
  font-size: 12px;
  color: #909399;
}

.search-empty {
  padding: 20px;
}

.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}
</style>
