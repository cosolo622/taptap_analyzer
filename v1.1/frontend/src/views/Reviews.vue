<template>
  <div class="reviews">
    <!-- 筛选区域 -->
    <el-card shadow="hover" class="filter-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="filter-item">
            <span class="filter-label">日期范围：</span>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="handleFilter"
              style="width: 100%;"
            />
          </div>
        </el-col>
        <el-col :span="4">
          <div class="filter-item">
            <span class="filter-label">问题大类：</span>
            <el-select v-model="selectedMainCategory" placeholder="全部" clearable @change="handleFilter" style="width: 100%;">
              <el-option v-for="cat in mainCategories" :key="cat" :label="cat" :value="cat" />
            </el-select>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="filter-item">
            <span class="filter-label">问题子类：</span>
            <el-select v-model="selectedSubCategory" placeholder="全部" clearable @change="handleFilter" style="width: 100%;">
              <el-option v-for="cat in filteredSubCategories" :key="cat" :label="cat" :value="cat" />
            </el-select>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="filter-item">
            <span class="filter-label">情感类型：</span>
            <el-select v-model="selectedSentiment" placeholder="全部" clearable @change="handleFilter" style="width: 100%;">
              <el-option label="正向" value="正向" />
              <el-option label="负向" value="负向" />
              <el-option label="中性" value="中性" />
            </el-select>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="filter-item">
            <span class="filter-label">星级：</span>
            <el-select v-model="selectedRating" placeholder="全部" clearable @change="handleFilter" style="width: 100%;">
              <el-option label="1星" :value="1" />
              <el-option label="2星" :value="2" />
              <el-option label="3星" :value="3" />
              <el-option label="4星" :value="4" />
              <el-option label="5星" :value="5" />
            </el-select>
          </div>
        </el-col>
      </el-row>
      <el-row style="margin-top: 15px;">
        <el-col :span="24">
          <div class="filter-item">
            <span class="filter-label">关键词搜索：</span>
            <el-input 
              v-model="searchKeyword" 
              placeholder="搜索评价内容、用户名" 
              clearable 
              @input="handleFilter"
              style="width: 300px;"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <span class="result-count">共 {{ filteredReviews.length }} 条结果</span>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 评价表格 -->
    <el-card shadow="hover" style="margin-top: 20px;">
      <el-table 
        :data="paginatedReviews" 
        stripe 
        style="width: 100%"
        max-height="600"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="日期" label="日期" width="120" sortable="custom" />
        <el-table-column prop="用户名" label="用户名" width="120" show-overflow-tooltip />
        <el-table-column prop="星级" label="星级" width="80" sortable="custom">
          <template #default="{ row }">
            <el-rate v-model="row['星级']" disabled :max="5" size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="情感" label="情感" width="100">
          <template #default="{ row }">
            <el-tag :type="getSentimentType(row['情感'])" size="small">
              {{ row['情感'] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="问题大类" label="问题大类" width="130">
          <template #default="{ row }">
            <span>{{ row['问题大类'] || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="问题子类" label="问题子类" width="150">
          <template #default="{ row }">
            <span>{{ row['问题子类'] || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="一句话摘要" label="一句话摘要" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showFullReview(row)">
              查看全文
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="filteredReviews.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 评价全文弹窗 -->
    <el-dialog v-model="dialogVisible" title="评价详情" width="600px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="日期">{{ currentReview['日期'] }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ currentReview['用户名'] }}</el-descriptions-item>
        <el-descriptions-item label="星级">
          <el-rate v-model="currentReview['星级']" disabled :max="5" />
        </el-descriptions-item>
        <el-descriptions-item label="情感">
          <el-tag :type="getSentimentType(currentReview['情感'])">{{ currentReview['情感'] }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="问题大类">{{ currentReview['问题大类'] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="问题子类">{{ currentReview['问题子类'] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="一句话摘要">{{ currentReview['一句话摘要'] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="评价全文">
          <div class="full-review-content">{{ currentReview['评价内容'] || '-' }}</div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps(['data'])

const dateRange = ref([])
const selectedMainCategory = ref('')
const selectedSubCategory = ref('')
const selectedSentiment = ref('')
const selectedRating = ref(null)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const dialogVisible = ref(false)
const currentReview = ref({})
const sortProp = ref('')
const sortOrder = ref('')

const processedReviews = computed(() => {
  if (!props.data?.reviews) return []
  return props.data.reviews.map(r => {
    const problemParts = (r['问题分类'] || '').split('-')
    return {
      ...r,
      '问题大类': problemParts[0]?.trim() || '',
      '问题子类': problemParts.length > 1 ? problemParts.slice(0, 2).join('-').trim() : ''
    }
  })
})

const mainCategories = computed(() => {
  const cats = new Set()
  processedReviews.value.forEach(r => {
    if (r['问题大类'] && r['问题大类'] !== '无问题') {
      cats.add(r['问题大类'])
    }
  })
  return Array.from(cats).sort()
})

const subCategories = computed(() => {
  const cats = new Set()
  processedReviews.value.forEach(r => {
    if (r['问题子类'] && !r['问题子类'].includes('无问题')) {
      cats.add(r['问题子类'])
    }
  })
  return Array.from(cats).sort()
})

const filteredSubCategories = computed(() => {
  if (!selectedMainCategory.value) return subCategories.value
  return subCategories.value.filter(cat => cat.startsWith(selectedMainCategory.value))
})

const filteredReviews = computed(() => {
  let result = processedReviews.value
  
  if (dateRange.value && dateRange.value.length === 2) {
    const [start, end] = dateRange.value
    result = result.filter(r => r['日期'] >= start && r['日期'] <= end)
  }
  
  if (selectedMainCategory.value) {
    result = result.filter(r => r['问题大类'] === selectedMainCategory.value)
  }
  
  if (selectedSubCategory.value) {
    result = result.filter(r => r['问题子类'] === selectedSubCategory.value)
  }
  
  if (selectedSentiment.value) {
    result = result.filter(r => r['情感'] === selectedSentiment.value)
  }
  
  if (selectedRating.value) {
    result = result.filter(r => r['星级'] === selectedRating.value)
  }
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(r => 
      (r['评价内容'] || '').toLowerCase().includes(keyword) ||
      (r['用户名'] || '').toLowerCase().includes(keyword) ||
      (r['一句话摘要'] || '').toLowerCase().includes(keyword)
    )
  }
  
  if (sortProp.value && sortOrder.value) {
    result = [...result].sort((a, b) => {
      const aVal = a[sortProp.value]
      const bVal = b[sortProp.value]
      if (sortOrder.value === 'ascending') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
  }
  
  return result
})

const paginatedReviews = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredReviews.value.slice(start, end)
})

const getSentimentType = (sentiment) => {
  const typeMap = {
    '正向': 'success',
    '负向': 'danger',
    '中性': 'info'
  }
  return typeMap[sentiment] || ''
}

const handleFilter = () => {
  currentPage.value = 1
}

const handleSortChange = ({ prop, order }) => {
  sortProp.value = prop
  sortOrder.value = order
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page) => {
  currentPage.value = page
}

const showFullReview = (row) => {
  currentReview.value = row
  dialogVisible.value = true
}

watch(() => props.data, () => {
  currentPage.value = 1
}, { deep: true })

onMounted(() => {
  currentPage.value = 1
})
</script>

<style scoped>
.reviews {
  padding: 0;
}

.filter-card {
  margin-bottom: 0;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-label {
  font-weight: 500;
  color: #606266;
  white-space: nowrap;
  font-size: 14px;
}

.result-count {
  margin-left: 20px;
  color: #909399;
  font-size: 14px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.full-review-content {
  max-height: 300px;
  overflow-y: auto;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
