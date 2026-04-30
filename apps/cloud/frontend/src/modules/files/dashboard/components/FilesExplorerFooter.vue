<script setup lang="ts">
import { ElIcon } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'

defineProps<{
  状态文案: string
  刷新中: boolean
}>()
</script>

<template>
  <div class="explorer-footer">
    <span class="explorer-footer__text">{{ 状态文案 }}</span>
    <div v-if="刷新中" class="explorer-footer__status" aria-label="正在刷新列表" role="status">
      <ElIcon class="explorer-footer__spinner is-loading" aria-hidden="true">
        <Loading />
      </ElIcon>
    </div>
  </div>
</template>

<style scoped>
.explorer-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
  color: var(--el-text-color-secondary);
  font-size: 12px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.explorer-footer__text {
  min-width: 0;
}

.explorer-footer__status {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  min-height: 20px;
}

.explorer-footer__spinner {
  font-size: 14px;
  color: var(--el-color-primary);
}
</style>
