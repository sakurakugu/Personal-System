<script setup lang="ts">
import { Histogram, Refresh } from '@element-plus/icons-vue'
import { 获取API错误消息 } from '@personal-system/api'
import { 获取仪表盘统计, type DashboardStats } from '@personal-system/domain/system'
import { AppIconButton, PageSectionShell } from '@personal-system/ui'
import { ElAlert, ElCard, ElSkeleton, ElStatistic, ElTooltip } from 'element-plus'
import { onMounted, ref } from 'vue'

withDefaults(
  defineProps<{
    showBack?: boolean
    backTo?: string
  }>(),
  {
    showBack: false,
    backTo: '/',
  },
)

const loading = ref(false)
const loadError = ref('')
const stats = ref<Pick<
  DashboardStats,
  | 'total_todos'
  | 'current_month_bill_income_cent'
  | 'current_month_bill_expense_cent'
  | 'current_month_bill_net_cent'
  | 'current_month_bill_record_count'
> | null>(null)

async function loadStats() {
  if (loading.value) return

  loading.value = true
  loadError.value = ''
  console.info('[数据统计] 开始加载')
  try {
    stats.value = await 获取仪表盘统计()
    console.info('[数据统计] 加载完成')
  } catch (error) {
    loadError.value = 获取API错误消息(error, '数据统计加载失败，请重试')
    console.error('[数据统计] 加载失败', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadStats()
})
</script>

<template>
  <div class="data-stats-page">
    <PageSectionShell title="数据统计" :icon="Histogram" :show-back="showBack" :to="backTo">
      <template #actions>
        <ElTooltip :content="loadError ? '重试' : '刷新'">
          <AppIconButton
            :label="loadError ? '重试加载数据统计' : '刷新数据统计'"
            :disabled="loading"
            @click="loadStats"
          >
            <Refresh />
          </AppIconButton>
        </ElTooltip>
      </template>
      <ElAlert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon />
      <ElSkeleton v-else :loading="loading" animated>
        <div v-if="stats" class="stats-summary">
          <ElCard shadow="never"><ElStatistic title="待办" :value="stats.total_todos" /></ElCard>
          <ElCard shadow="never">
            <ElStatistic
              title="本月收入"
              :value="stats.current_month_bill_income_cent / 100"
              :precision="2"
            >
              <template #suffix>元</template>
            </ElStatistic>
          </ElCard>
          <ElCard shadow="never">
            <ElStatistic
              title="本月支出"
              :value="stats.current_month_bill_expense_cent / 100"
              :precision="2"
            >
              <template #suffix>元</template>
            </ElStatistic>
          </ElCard>
          <ElCard shadow="never">
            <ElStatistic
              title="本月结余"
              :value="stats.current_month_bill_net_cent / 100"
              :precision="2"
            >
              <template #suffix>元</template>
            </ElStatistic>
          </ElCard>
          <ElCard shadow="never">
            <ElStatistic title="本月记账笔数" :value="stats.current_month_bill_record_count" />
          </ElCard>
        </div>
      </ElSkeleton>
    </PageSectionShell>
  </div>
</template>

<style scoped>
.data-stats-page {
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.stats-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stats-summary :deep(.el-card) {
  min-width: 0;
  border-radius: 8px;
}

.stats-summary :deep(.el-statistic__content) {
  overflow-wrap: anywhere;
}

@media (max-width: 1100px) {
  .stats-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .data-stats-page {
    padding: 16px;
  }

  .stats-summary {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
