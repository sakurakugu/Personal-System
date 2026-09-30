<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElAlert, ElCard, ElCol, ElRow, ElSkeleton, ElStatistic } from 'element-plus'
import { Histogram } from '@element-plus/icons-vue'
import { PageSectionShell } from '@personal-system/ui'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import type { EChartsOption } from 'echarts'
import VChart from 'vue-echarts'
import { 获取仪表盘统计 } from '../../api'
import type { DashboardStats } from '../../types'
import { 使用主题存储 } from '../../../../shared/stores/theme'

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent])
const themeStore = 使用主题存储()

const loading = ref(true)
const loadError = ref(false)
type 博客仪表盘统计 = Pick<DashboardStats, 'total_articles' | 'total_views' | 'recent_views'>
const stats = ref<博客仪表盘统计>({
  total_articles: 0,
  total_views: 0,
  recent_views: [],
})

const chartOption = ref<EChartsOption>({})

function readThemeColor(name: string, fallback: string) {
  if (typeof window === 'undefined') {
    return fallback
  }

  return window.getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

function buildChartOption(data: 博客仪表盘统计): EChartsOption {
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
    const data = await 获取仪表盘统计()
    stats.value = data
    chartOption.value = buildChartOption(data)
  } catch (error) {
    loadError.value = true
    console.error('博客统计加载失败', error)
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
    <PageSectionShell title="博客统计" :icon="Histogram" title-tag="h2">
      <ElAlert v-if="loadError" title="博客统计加载失败，请刷新页面重试" type="error" :closable="false" show-icon />
      <ElSkeleton v-else :loading="loading" animated>
        <ElRow :gutter="16" class="stats-summary-row">
          <ElCol :xs="24" :sm="12" :lg="6">
            <ElCard><ElStatistic title="文章" :value="stats.total_articles" /></ElCard>
          </ElCol>
          <ElCol :xs="24" :sm="12" :lg="6">
            <ElCard><ElStatistic title="浏览量" :value="stats.total_views" /></ElCard>
          </ElCol>
        </ElRow>

        <ElCard header="最近7天文章访问趋势" style="margin-top: 24px">
          <VChart v-if="stats.recent_views.length" :option="chartOption" style="height: 300px" autoresize />
          <div v-else style="text-align: center; padding: 40px; color: #999">暂无数据</div>
        </ElCard>
      </ElSkeleton>
    </PageSectionShell>
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
