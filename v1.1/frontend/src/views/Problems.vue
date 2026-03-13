<template>
  <div class="problems">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>问题大类分布</span>
          </template>
          <div ref="pieChart" style="height: 400px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>问题大类TOP10</span>
          </template>
          <div ref="barChart" style="height: 400px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>问题分类层级汇总</span>
              <el-input v-model="searchText" placeholder="搜索问题" style="width: 200px;" clearable>
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>
          </template>
          <el-table 
            :data="filteredData" 
            stripe 
            style="width: 100%"
            max-height="500"
          >
            <el-table-column prop="大类" label="大类" width="150" />
            <el-table-column prop="大类出现次数" label="大类次数" width="100" />
            <el-table-column prop="标准子类" label="标准子类" width="200" />
            <el-table-column prop="标准子类出现次数" label="子类次数" width="100" />
            <el-table-column prop="原子类（子子类）" label="原子类" />
            <el-table-column prop="原子类出现次数" label="原子类次数" width="100" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const props = defineProps(['data'])
const searchText = ref('')
const pieChart = ref(null)
const barChart = ref(null)

const filteredData = computed(() => {
  if (!props.data?.hierarchy) return []
  if (!searchText.value) return props.data.hierarchy
  return props.data.hierarchy.filter(item => 
    item['大类']?.includes(searchText.value) ||
    item['标准子类']?.includes(searchText.value) ||
    item['原子类（子子类）']?.includes(searchText.value)
  )
})

const initCharts = () => {
  if (!props.data?.mainCategories) return

  const pieChartInstance = echarts.init(pieChart.value)
  pieChartInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}次 ({d}%)' },
    legend: { type: 'scroll', bottom: '5%' },
    series: [{
      type: 'pie',
      radius: ['30%', '60%'],
      data: props.data.mainCategories.slice(0, 10).map(c => ({ name: c['大类'], value: c['出现次数'] })),
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  })

  const barChartInstance = echarts.init(barChart.value)
  barChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: props.data.mainCategories.slice(0, 10).map(c => c['大类']).reverse() },
    series: [{
      type: 'bar',
      data: props.data.mainCategories.slice(0, 10).map(c => c['出现次数']).reverse(),
      itemStyle: { borderRadius: [0, 4, 4, 0] }
    }]
  })
}

watch(() => props.data, initCharts, { deep: true })
onMounted(initCharts)
</script>

<style scoped>
.problems {
  padding: 0;
}
</style>
