<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElCard, ElCol, ElIcon, ElRow, ElSkeleton, ElStatistic } from 'element-plus'
import { Histogram } from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import api from '../../utils/api'

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent])

const loading = ref(true)
const stats = ref<any>({ total_articles: 0, total_comments: 0, total_views: 0, total_todos: 0, recent_views: [] })

const chartOption = ref({})

onMounted(async () => {
  try {
    const { data } = await api.get('/stats/dashboard')
    stats.value = data
    chartOption.value = {
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: data.recent_views.map((v: any) => v.date),
      },
      yAxis: { type: 'value' },
      series: [{
        data: data.recent_views.map((v: any) => v.count),
        type: 'bar',
        itemStyle: { color: '#18a058' },
      }],
    }
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <h2 style="display: flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><Histogram /></ElIcon>
      <span>数据统计</span>
    </h2>
    <ElSkeleton :loading="loading" animated>
      <ElRow :gutter="16">
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard><ElStatistic label="文章" :value="stats.total_articles" /></ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard><ElStatistic label="评论" :value="stats.total_comments" /></ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard><ElStatistic label="浏览量" :value="stats.total_views" /></ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard><ElStatistic label="待办" :value="stats.total_todos" /></ElCard>
        </ElCol>
      </ElRow>

      <ElCard header="最近7天访问趋势" style="margin-top: 24px">
        <VChart v-if="stats.recent_views.length" :option="chartOption" style="height: 300px" autoresize />
        <div v-else style="text-align: center; padding: 40px; color: #999">暂无数据</div>
      </ElCard>
    </ElSkeleton>
  </div>
</template>
