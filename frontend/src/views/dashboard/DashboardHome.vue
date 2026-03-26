<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElCard, ElCol, ElIcon, ElRow, ElSkeleton, ElStatistic } from 'element-plus'
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
  <div class="page-container">
    <h2 style="display: flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><DataBoard /></ElIcon>
      <span>个人看板</span>
    </h2>
    <ElSkeleton :loading="loading" animated>
      <ElRow :gutter="16">
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard>
            <ElStatistic class="dashboard-stat" label="文章总数" :value="stats.total_articles">
              <template #prefix><ElIcon class="stat-prefix-icon"><Document /></ElIcon></template>
            </ElStatistic>
          </ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard>
            <ElStatistic class="dashboard-stat" label="评论总数" :value="stats.total_comments">
              <template #prefix><ElIcon class="stat-prefix-icon"><ChatDotRound /></ElIcon></template>
            </ElStatistic>
          </ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard>
            <ElStatistic class="dashboard-stat" label="总浏览量" :value="stats.total_views">
              <template #prefix><ElIcon class="stat-prefix-icon"><View /></ElIcon></template>
            </ElStatistic>
          </ElCard>
        </ElCol>
        <ElCol :xs="24" :sm="12" :lg="6">
          <ElCard>
            <ElStatistic class="dashboard-stat" label="待办事项" :value="stats.total_todos">
              <template #prefix><ElIcon class="stat-prefix-icon"><Check /></ElIcon></template>
            </ElStatistic>
          </ElCard>
        </ElCol>
      </ElRow>
    </ElSkeleton>
  </div>
</template>

<style scoped>
.dashboard-stat :deep(.el-statistic__content) {
  display: flex;
  align-items: center;
}

.dashboard-stat :deep(.el-statistic__head) {
  margin-bottom: 6px;
}

.dashboard-stat :deep(.el-statistic__content-prefix) {
  display: inline-flex;
  align-items: center;
  margin-right: 6px;
}

.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.stat-prefix-icon {
  display: inline-flex;
  align-items: center;
  line-height: 1;
}
</style>
