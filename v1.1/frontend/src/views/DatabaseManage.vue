<template>
  <div class="database-manage">
    <el-card class="section-card">
      <template #header>
        <div class="card-header">
          <span>数据库概览</span>
          <el-button type="primary" size="small" @click="loadOverview" :loading="loadingOverview">刷新</el-button>
        </div>
      </template>
      <el-table :data="tables" stripe>
        <el-table-column prop="table_name" label="表名" width="180" />
        <el-table-column prop="row_count" label="记录数" width="120" />
        <el-table-column prop="column_count" label="字段数" width="120" />
        <el-table-column label="字段结构">
          <template #default="{ row }">
            <div class="columns-inline">
              {{ (row.columns || []).map(c => `${c.name}:${c.type}`).join(' | ') }}
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="section-card">
      <template #header>
        <span>SQL查询</span>
      </template>
      <el-input v-model="sql" type="textarea" :rows="4" placeholder="请输入SELECT/WITH/EXPLAIN查询" />
      <div class="action-row">
        <el-input-number v-model="sqlLimit" :min="1" :max="1000" />
        <el-button type="primary" @click="runSql" :loading="runningSql">执行查询</el-button>
      </div>
      <el-table v-if="sqlRows.length > 0" :data="sqlRows" max-height="360" stripe>
        <el-table-column v-for="col in sqlColumns" :key="col" :prop="col" :label="col" min-width="140" show-overflow-tooltip />
      </el-table>
    </el-card>

    <el-card class="section-card">
      <template #header>
        <span>去重工具</span>
      </template>
      <el-form label-width="120px">
        <el-form-item label="产品">
          <el-select v-model="dedupeProductId" clearable placeholder="全部产品" style="width: 240px">
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="去重字段">
          <el-checkbox-group v-model="dedupeFields">
            <el-checkbox label="name">用户名</el-checkbox>
            <el-checkbox label="date">日期</el-checkbox>
            <el-checkbox label="content">内容</el-checkbox>
            <el-checkbox label="rating">星级</el-checkbox>
            <el-checkbox label="review_id">评论ID</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item>
          <el-button type="warning" @click="runDedupe" :loading="runningDedupe">执行去重</el-button>
          <span class="tip">默认推荐：用户名+日期+内容</span>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="section-card">
      <template #header>
        <span>按日期删除</span>
      </template>
      <el-form label-width="120px">
        <el-form-item label="产品">
          <el-select v-model="deleteProductId" placeholder="请选择产品" style="width: 240px">
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="deleteDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 320px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="danger" @click="runDeleteByDate" :loading="runningDelete">删除</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const loadingOverview = ref(false)
const runningSql = ref(false)
const runningDedupe = ref(false)
const runningDelete = ref(false)

const tables = ref([])
const products = ref([])
const sql = ref('select * from reviews order by id desc')
const sqlLimit = ref(50)
const sqlColumns = ref([])
const sqlRows = ref([])

const dedupeProductId = ref(null)
const dedupeFields = ref(['name', 'date', 'content'])

const deleteProductId = ref(null)
const deleteDateRange = ref([])

const loadProducts = async () => {
  const res = await api.get('/products')
  products.value = res.data.products || []
  if (!deleteProductId.value && products.value.length > 0) {
    deleteProductId.value = products.value[0].id
  }
}

const loadOverview = async () => {
  loadingOverview.value = true
  try {
    const res = await api.get('/admin/db/overview')
    tables.value = res.data.tables || []
  } catch (error) {
    ElMessage.error('读取数据库概览失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loadingOverview.value = false
  }
}

const runSql = async () => {
  runningSql.value = true
  try {
    const res = await api.post('/admin/db/query', {
      sql: sql.value,
      limit: sqlLimit.value
    })
    sqlColumns.value = res.data.columns || []
    sqlRows.value = res.data.rows || []
    ElMessage.success(`查询成功，返回 ${res.data.count || 0} 行`)
  } catch (error) {
    ElMessage.error('SQL执行失败：' + (error.response?.data?.detail || error.message))
  } finally {
    runningSql.value = false
  }
}

const runDedupe = async () => {
  if (!dedupeFields.value.length) {
    ElMessage.warning('请至少选择一个去重字段')
    return
  }
  await ElMessageBox.confirm('确认执行去重吗？该操作会直接删除重复数据。', '确认去重', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
  runningDedupe.value = true
  try {
    const res = await api.post('/admin/db/deduplicate', {
      fields: dedupeFields.value,
      product_id: dedupeProductId.value
    })
    ElMessage.success(`去重完成，删除 ${res.data.deleted || 0} 条`)
    await loadOverview()
  } catch (error) {
    ElMessage.error('去重失败：' + (error.response?.data?.detail || error.message))
  } finally {
    runningDedupe.value = false
  }
}

const runDeleteByDate = async () => {
  if (!deleteProductId.value || !deleteDateRange.value?.length) {
    ElMessage.warning('请先选择产品和日期范围')
    return
  }
  await ElMessageBox.confirm('确认删除该日期范围的数据吗？', '确认删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
  runningDelete.value = true
  try {
    const [start, end] = deleteDateRange.value
    const res = await api.post('/admin/db/delete-by-date', {
      product_id: deleteProductId.value,
      start_date: start,
      end_date: end
    })
    ElMessage.success(`删除完成，共删除 ${res.data.deleted || 0} 条`)
    await loadOverview()
  } catch (error) {
    ElMessage.error('删除失败：' + (error.response?.data?.detail || error.message))
  } finally {
    runningDelete.value = false
  }
}

onMounted(async () => {
  await loadProducts()
  await loadOverview()
})
</script>

<style scoped>
.database-manage {
  padding: 0;
}
.section-card {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.action-row {
  margin: 12px 0;
  display: flex;
  gap: 12px;
  align-items: center;
}
.columns-inline {
  font-size: 12px;
  color: #606266;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tip {
  margin-left: 12px;
  color: #909399;
}
</style>
