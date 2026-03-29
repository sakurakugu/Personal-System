<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElCard, ElCol, ElIcon, ElRow, ElSkeleton, ElStatistic } from 'element-plus'
import { DataBoard, Document, ChatDotRound, View, Check } from '@element-plus/icons-vue'
import { fetchDashboardStats } from '../../features/system/api'
import type { DashboardStats } from '../../features/system/types'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
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
const loading = ref(true)

const displayName = computed(() => auth.user?.nickname?.trim() || auth.user?.username || '你')

const welcomeText = computed(() => `${displayName.value}，这里汇总了你当前账号的内容、互动与任务状态。`)

const recentViewCount = computed(() => stats.value.recent_views.reduce((sum, item) => sum + item.count, 0))

function formatCurrency(cents: number): string {
  return `¥${(cents / 100).toFixed(2)}`
}

const overviewText = computed(() => {
  if (recentViewCount.value > 0) {
    return `最近 7 天累计记录 ${recentViewCount.value} 次访问，本月账单已记 ${stats.value.current_month_bill_record_count} 笔，可同时观察内容反馈和资金流向。`
  }
  if (stats.value.total_articles > 0 || stats.value.total_todos > 0 || stats.value.current_month_bill_record_count > 0) {
    return '当前已经有基础数据沉淀，但最近 7 天还没有新的访问记录，可以继续发布内容、推进待办或补全账单。'
  }
  return '当前还没有可展示的活跃数据，适合先创建文章、补充资料、添加待办或开始记账。'
})

const statCards = computed(() => [
  {
    key: 'articles',
    title: '文章总数',
    value: stats.value.total_articles,
    precision: 0,
    icon: Document,
    caption:
      stats.value.total_articles > 0
        ? `当前已累计 ${stats.value.total_articles} 篇文章，可以继续更新旧文或新增内容。`
        : '当前还没有文章，建议先创建一篇草稿作为起点。',
  },
  {
    key: 'comments',
    title: '评论总数',
    value: stats.value.total_comments,
    precision: 0,
    icon: ChatDotRound,
    caption:
      stats.value.total_comments > 0
        ? `共收到 ${stats.value.total_comments} 条评论，说明已有用户互动。`
        : '暂时还没有评论，可以先发布内容再观察互动情况。',
  },
  {
    key: 'views',
    title: '总浏览量',
    value: stats.value.total_views,
    precision: 0,
    icon: View,
    caption:
      stats.value.total_views > 0
        ? `累计浏览 ${stats.value.total_views} 次，可用于判断内容曝光表现。`
        : '暂时还没有浏览记录，发布内容后这里会逐步积累。',
  },
  {
    key: 'todos',
    title: '待办事项',
    value: stats.value.total_todos,
    precision: 0,
    icon: Check,
    caption:
      stats.value.total_todos > 0
        ? `当前有 ${stats.value.total_todos} 个待办，记得及时处理高优先级任务。`
        : '当前没有待办事项，节奏比较干净，也可以补充后续计划。',
  },
  {
    key: 'bill-income',
    title: '本月收入',
    value: stats.value.current_month_bill_income_cent / 100,
    precision: 2,
    suffix: '元',
    icon: DataBoard,
    caption:
      stats.value.current_month_bill_record_count > 0
        ? `本月收入 ${formatCurrency(stats.value.current_month_bill_income_cent)}，支出 ${formatCurrency(stats.value.current_month_bill_expense_cent)}。`
        : '本月还没有账单记录，进入账单页后可以开始记账。',
  },
  {
    key: 'bill-expense',
    title: '本月结余',
    value: stats.value.current_month_bill_net_cent / 100,
    precision: 2,
    suffix: '元',
    icon: DataBoard,
    caption:
      stats.value.current_month_bill_record_count > 0
        ? `当前净额为 ${formatCurrency(stats.value.current_month_bill_net_cent)}，已累计记账 ${stats.value.current_month_bill_record_count} 笔。`
        : '账单数据为空时，这里会在记账后自动汇总本月净额。',
  },
])

onMounted(async () => {
  try {
    await auth.restoreUserIfNeeded()
    stats.value = await fetchDashboardStats()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-container">
    <section class="dashboard-hero">
      <h2 class="dashboard-title">
        <ElIcon><DataBoard /></ElIcon>
        <span>个人看板</span>
      </h2>
      <p class="dashboard-hero-headline">{{ welcomeText }}</p>
      <p class="dashboard-hero-description">{{ overviewText }}</p>
    </section>

    <ElSkeleton :loading="loading" animated>
      <ElRow :gutter="16" class="stats-grid">
        <ElCol v-for="card in statCards" :key="card.key" :xs="24" :sm="12" :lg="8">
          <ElCard class="stat-card">
            <ElStatistic class="dashboard-stat" :value="card.value" :precision="card.precision">
              <template #prefix>
                <div class="stat-prefix">
                  <ElIcon class="stat-prefix-icon"><component :is="card.icon" /></ElIcon>
                  <span class="stat-prefix-text">{{ card.title }}</span>
                </div>
              </template>
              <template v-if="card.suffix" #suffix>{{ card.suffix }}</template>
            </ElStatistic>
            <p class="stat-caption">{{ card.caption }}</p>
          </ElCard>
        </ElCol>
      </ElRow>

      <ElCard class="dashboard-note">
        <div class="dashboard-note-title">概览说明</div>
        <p class="dashboard-note-text">
          文章与浏览量用于观察内容沉淀，评论反映互动情况，待办帮助跟进执行节奏，账单则补充了本月资金流向。
        </p>
      </ElCard>
    </ElSkeleton>
  </div>
</template>

<style scoped>
.dashboard-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.dashboard-hero {
  margin-bottom: 24px;
  padding: 24px;
  border: 1px solid rgba(24, 160, 88, 0.16);
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(24, 160, 88, 0.12), rgba(24, 160, 88, 0.03)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.98));
}

.dashboard-hero-headline {
  margin: 14px 0 8px;
  font-size: 20px;
  font-weight: 600;
  line-height: 1.5;
}

.dashboard-hero-description {
  margin: 0;
  color: var(--el-text-color-secondary);
  line-height: 1.75;
}

.stats-grid {
  margin-bottom: 16px;
}

.stat-card {
  height: 100%;
}

.dashboard-stat :deep(.el-statistic__content) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
}

.dashboard-stat :deep(.el-statistic__content-prefix) {
  display: flex;
  min-width: 0;
}

.stat-prefix {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

:deep(.el-card) {
  border-radius: 12px;
}

.stat-caption {
  margin: 12px 0 0;
  color: var(--el-text-color-secondary);
  line-height: 1.7;
  min-height: 48px;
}

.dashboard-note-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.dashboard-note-text {
  margin: 0;
  color: var(--el-text-color-secondary);
  line-height: 1.75;
}

.stat-prefix-icon {
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.stat-prefix-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dark .dashboard-hero {
  border-color: rgba(120, 214, 163, 0.16);
  background:
    linear-gradient(135deg, rgba(24, 160, 88, 0.18), rgba(24, 160, 88, 0.06)),
    rgba(18, 25, 22, 0.92);
}
</style>
