<template>
  <div class="alert-settings">
    <!-- 预警规则列表 -->
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>预警规则设置</span>
          <el-button type="primary" @click="addRule">
            <el-icon><Plus /></el-icon>
            添加规则
          </el-button>
        </div>
      </template>
      
      <el-table :data="alertRules" stripe style="width: 100%">
        <el-table-column prop="name" label="规则名称" width="180" />
        <el-table-column label="触发条件" width="300">
          <template #default="{ row }">
            当最近 {{ row.days }} 天的 {{ getMetricName(row.metric) }} {{ row.operator === 'gt' ? '>' : '<' }} {{ row.threshold }} 时触发
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="updateRule(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="triggered" label="预警状态" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.triggered" type="danger" effect="dark">
              <el-icon><Warning /></el-icon>
              已触发
            </el-tag>
            <el-tag v-else type="success">正常</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lastTriggerTime" label="上次触发" width="180">
          <template #default="{ row }">
            {{ row.lastTriggerTime || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editRule(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="deleteRule(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑规则弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingRule ? '编辑规则' : '添加规则'" width="500px">
      <el-form :model="ruleForm" label-width="100px">
        <el-form-item label="规则名称">
          <el-input v-model="ruleForm.name" placeholder="如：负面评价数预警" />
        </el-form-item>
        <el-form-item label="统计周期">
          <el-select v-model="ruleForm.days" style="width: 100%;">
            <el-option :value="1" label="最近1天" />
            <el-option :value="3" label="最近3天" />
            <el-option :value="7" label="最近7天" />
            <el-option :value="14" label="最近14天" />
            <el-option :value="30" label="最近30天" />
          </el-select>
        </el-form-item>
        <el-form-item label="监控指标">
          <el-select v-model="ruleForm.metric" style="width: 100%;">
            <el-option value="negativeCount" label="负面评价数" />
            <el-option value="positiveCount" label="正向评价数" />
            <el-option value="totalCount" label="总评价数" />
            <el-option value="avgRating" label="平均星级" />
            <el-option value="negativeRate" label="负面评价占比(%)" />
          </el-select>
        </el-form-item>
        <el-form-item label="触发条件">
          <el-row :gutter="10">
            <el-col :span="8">
              <el-select v-model="ruleForm.operator" style="width: 100%;">
                <el-option value="gt" label="大于" />
                <el-option value="lt" label="小于" />
              </el-select>
            </el-col>
            <el-col :span="16">
              <el-input-number v-model="ruleForm.threshold" :min="0" :precision="ruleForm.metric === 'avgRating' ? 1 : 0" style="width: 100%;" />
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="ruleForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRule">保存</el-button>
      </template>
    </el-dialog>

    <!-- 预警记录 -->
    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <span>预警记录</span>
      </template>
      <el-table :data="alertHistory" stripe style="width: 100%">
        <el-table-column prop="ruleName" label="规则名称" width="180" />
        <el-table-column prop="triggerTime" label="触发时间" width="180" />
        <el-table-column prop="metric" label="监控指标" width="150">
          <template #default="{ row }">
            {{ getMetricName(row.metric) }}
          </template>
        </el-table-column>
        <el-table-column prop="actualValue" label="实际值" width="100" />
        <el-table-column prop="threshold" label="阈值" width="100" />
        <el-table-column prop="status" label="处理状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'handled' ? 'success' : 'warning'">
              {{ row.status === 'handled' ? '已处理' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button v-if="row.status !== 'handled'" type="primary" link size="small" @click="handleAlert(row)">
              标记处理
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Plus, Warning } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const emit = defineEmits(['alert-change'])

const alertRules = ref([
  {
    id: 1,
    name: '负面评价数预警',
    days: 7,
    metric: 'negativeCount',
    operator: 'gt',
    threshold: 50,
    enabled: true,
    triggered: false,
    lastTriggerTime: '2026-02-20 10:30'
  },
  {
    id: 2,
    name: '平均星级预警',
    days: 3,
    metric: 'avgRating',
    operator: 'lt',
    threshold: 3.0,
    enabled: true,
    triggered: true,
    lastTriggerTime: '2026-02-23 15:20'
  }
])

const alertHistory = ref([
  {
    id: 1,
    ruleName: '平均星级预警',
    triggerTime: '2026-02-23 15:20',
    metric: 'avgRating',
    actualValue: 2.8,
    threshold: 3.0,
    status: 'pending'
  },
  {
    id: 2,
    ruleName: '负面评价数预警',
    triggerTime: '2026-02-20 10:30',
    metric: 'negativeCount',
    actualValue: 58,
    threshold: 50,
    status: 'handled'
  }
])

const dialogVisible = ref(false)
const editingRule = ref(null)
const ruleForm = ref({
  name: '',
  days: 7,
  metric: 'negativeCount',
  operator: 'gt',
  threshold: 50,
  enabled: true
})

const metricNames = {
  negativeCount: '负面评价数',
  positiveCount: '正向评价数',
  totalCount: '总评价数',
  avgRating: '平均星级',
  negativeRate: '负面评价占比'
}

const getMetricName = (metric) => metricNames[metric] || metric

const addRule = () => {
  editingRule.value = null
  ruleForm.value = {
    name: '',
    days: 7,
    metric: 'negativeCount',
    operator: 'gt',
    threshold: 50,
    enabled: true
  }
  dialogVisible.value = true
}

const editRule = (row) => {
  editingRule.value = row
  ruleForm.value = { ...row }
  dialogVisible.value = true
}

const saveRule = () => {
  if (!ruleForm.value.name) {
    ElMessage.warning('请输入规则名称')
    return
  }
  
  if (editingRule.value) {
    Object.assign(editingRule.value, ruleForm.value)
    ElMessage.success('规则更新成功')
  } else {
    alertRules.value.push({
      id: Date.now(),
      ...ruleForm.value,
      triggered: false,
      lastTriggerTime: null
    })
    ElMessage.success('规则添加成功')
  }
  
  dialogVisible.value = false
  saveToStorage()
}

const deleteRule = (row) => {
  ElMessageBox.confirm('确定删除该规则吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    const index = alertRules.value.findIndex(r => r.id === row.id)
    if (index > -1) {
      alertRules.value.splice(index, 1)
      saveToStorage()
      ElMessage.success('删除成功')
    }
  }).catch(() => {})
}

const updateRule = (row) => {
  saveToStorage()
}

const handleAlert = (row) => {
  row.status = 'handled'
  ElMessage.success('已标记为已处理')
}

const saveToStorage = () => {
  localStorage.setItem('alertRules', JSON.stringify(alertRules.value))
  emit('alert-change', alertRules.value)
}

const loadFromStorage = () => {
  const saved = localStorage.getItem('alertRules')
  if (saved) {
    alertRules.value = JSON.parse(saved)
  }
  emit('alert-change', alertRules.value)
}

watch(alertRules, () => {
  emit('alert-change', alertRules.value)
}, { deep: true })

onMounted(() => {
  loadFromStorage()
})
</script>

<style scoped>
.alert-settings {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
