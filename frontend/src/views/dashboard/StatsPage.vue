<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElCard, ElCol, ElIcon, ElRow, ElSkeleton, ElStatistic } from 'element-plus'
import { Histogram } from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import type { EChartsOption } from 'echarts'
import VChart from 'vue-echarts'
import { fetchDashboardStats } from '../../features/system/api'
import type { DashboardStats } from '../../features/system/types'
import { useThemeStore } from '../../stores/theme'

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent])
const themeStore = useThemeStore()

const loading = ref(true)
const stats = ref<DashboardStats>({
  total_articles: 0,
  total_comments: 0,
  total_views: 0,
  total_todos: 0,
  current_month_bill_income_cent: 0,
  current_month_bill_expense_cent: 0,
  current_month_bill_net_cent: 0,
  current_month_bill_record_count: 0,
  recent_views: [],
})

const chartOption = ref<EChartsOption>({})

function readThemeColor(name: string, fallback: string) {
  if (typeof window === 'undefined') {
    return fallback
  }

  return window.getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

function buildChartOption(data: DashboardStats): EChartsOption {
  return {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: data.recent_views.map((item) => item.date),
    },
    yAxis: { type: 'value' },
    series: [{
      data: data.recent_views.map((item) => item.count),
      type: 'bar',
      itemStyle: { color: readThemeColor('--el-color-primary', '#18a058') },
    }],
  }
}

onMounted(async () => {
  try {
    const data = await fetchDashboardStats()
    stats.value = data
    chartOption.value = buildChartOption(data)
  } finally {
    loading.value = false
  }
})

watch([() => themeStore.hue, () => themeStore.isDark], () => {
  if (stats.value.recent_views.length) {
    chartOption.value = buildChartOption(stats.value)
  }
})
</script>

<template>
  <div class="page-container">
    <h2 style="display: flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><Histogram /></ElIcon>
      <span>数据统计</span>
    </h2>
    <ElSkeleton :loading="loading" animated>
      <ElRow :gutter="16" class="stats-summary-row">
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard><ElStatistic title="文章" :value="stats.total_articles" /></ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard><ElStatistic title="评论" :value="stats.total_comments" /></ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard><ElStatistic title="浏览量" :value="stats.total_views" /></ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard><ElStatistic title="待办" :value="stats.total_todos" /></ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard>
            <ElStatistic title="本月收入" :value="stats.current_month_bill_income_cent / 100" :precision="2">
              <template #suffix>元</template>
            </ElStatistic>
          </ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard>
            <ElStatistic title="本月支出" :value="stats.current_month_bill_expense_cent / 100" :precision="2">
              <template #suffix>元</template>
            </ElStatistic>
          </ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard>
            <ElStatistic title="本月结余" :value="stats.current_month_bill_net_cent / 100" :precision="2">
              <template #suffix>元</template>
            </ElStatistic>
          </ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard><ElStatistic title="本月记账笔数" :value="stats.current_month_bill_record_count" /></ElCard>
        </ElCol>
      </ElRow>

      <ElCard header="最近7天文章访问趋势" style="margin-top: 24px">
        <VChart v-if="stats.recent_views.length" :option="chartOption" style="height: 300px" autoresize />
        <div v-else style="text-align: center; padding: 40px; color: #999">暂无数据</div>
      </ElCard>
    </ElSkeleton>
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

:deep(.el-card) {
  border-radius: 12px;
}

:deep(.stats-summary-row) {
  row-gap: 16px;
}
</style>
