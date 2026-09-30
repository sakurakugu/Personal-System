<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElAlert, ElCard, ElCol, ElRow, ElSkeleton, ElStatistic } from 'element-plus'
import { Histogram } from '@element-plus/icons-vue'
import { PageSectionShell } from '@personal-system/ui'
import { 获取仪表盘统计 } from '../../api'
import type { DashboardStats } from '../../types'

const loading = ref(true)
const loadError = ref(false)
const stats = ref<Pick<DashboardStats,
  | 'total_todos'
  | 'current_month_bill_income_cent'
  | 'current_month_bill_expense_cent'
  | 'current_month_bill_net_cent'
  | 'current_month_bill_record_count'
>>({
  total_todos: 0,
  current_month_bill_income_cent: 0,
  current_month_bill_expense_cent: 0,
  current_month_bill_net_cent: 0,
  current_month_bill_record_count: 0,
})

onMounted(async () => {
  try {
    stats.value = await 获取仪表盘统计()
  } catch (error) {
    loadError.value = true
    console.error('数据统计加载失败', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-container">
    <PageSectionShell title="数据统计" :icon="Histogram" title-tag="h2">
      <ElAlert v-if="loadError" title="数据统计加载失败，请刷新页面重试" type="error" :closable="false" show-icon />
      <ElSkeleton v-else :loading="loading" animated>
        <ElRow :gutter="16" class="stats-summary-row">
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
