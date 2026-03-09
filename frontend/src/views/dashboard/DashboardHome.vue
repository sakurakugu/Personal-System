<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NCard, NGrid, NGridItem, NStatistic, NSpin } from 'naive-ui'
import { ElIcon } from 'element-plus'
import { DataBoard, Document, ChatDotRound, View, Check } from '@element-plus/icons-vue'
import api from '../../utils/api'

const stats = ref({ total_articles: 0, total_comments: 0, total_views: 0, total_todos: 0 })
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.get('/stats/dashboard')
    stats.value = data
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <h2 style="display: flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><DataBoard /></ElIcon>
      <span>个人看板</span>
    </h2>
    <NSpin :show="loading">
      <NGrid :cols="4" :x-gap="16" :y-gap="16" responsive="screen" :item-responsive="true">
        <NGridItem span="0:4 640:2 1024:1">
          <NCard>
            <NStatistic class="dashboard-stat" label="文章总数" :value="stats.total_articles">
              <template #prefix>
                <ElIcon class="stat-prefix-icon"><Document /></ElIcon>
              </template>
            </NStatistic>
          </NCard>
        </NGridItem>
        <NGridItem span="0:4 640:2 1024:1">
          <NCard>
            <NStatistic class="dashboard-stat" label="评论总数" :value="stats.total_comments">
              <template #prefix>
                <ElIcon class="stat-prefix-icon"><ChatDotRound /></ElIcon>
              </template>
            </NStatistic>
          </NCard>
        </NGridItem>
        <NGridItem span="0:4 640:2 1024:1">
          <NCard>
            <NStatistic class="dashboard-stat" label="总浏览量" :value="stats.total_views">
              <template #prefix>
                <ElIcon class="stat-prefix-icon"><View /></ElIcon>
              </template>
            </NStatistic>
          </NCard>
        </NGridItem>
        <NGridItem span="0:4 640:2 1024:1">
          <NCard>
            <NStatistic class="dashboard-stat" label="待办事项" :value="stats.total_todos">
              <template #prefix>
                <ElIcon class="stat-prefix-icon"><Check /></ElIcon>
              </template>
            </NStatistic>
          </NCard>
        </NGridItem>
      </NGrid>
    </NSpin>
  </div>
</template>

<style scoped>
.dashboard-stat :deep(.n-statistic-value) {
  display: flex;
  align-items: center;
}

.dashboard-stat :deep(.n-statistic-value__prefix) {
  display: inline-flex;
  align-items: center;
  margin-right: 6px;
}

.stat-prefix-icon {
  display: inline-flex;
  align-items: center;
  line-height: 1;
}
</style>
