<script setup lang="ts">
import { ElButton } from 'element-plus'

defineProps<{
  已选资源总数: number
  是否已全选当前页: boolean
  当前选择可移动: boolean
  当前选择可编辑: boolean
  当前选择可下载: boolean
  是否全局搜索模式: boolean
  下载操作按钮文案: string
  已选资源移动文案: string
  已选资源重命名文案: string
  已选资源删除文案: string
}>()

const emit = defineEmits<{
  'toggle-select-page': []
  'clear-selection': []
  download: []
  'open-move': []
  'open-batch-rename': []
  delete: []
}>()
</script>

<template>
  <div v-if="已选资源总数 > 0" class="selection-toolbar">
    <div class="selection-toolbar__summary">
      <span>已选择 {{ 已选资源总数 }} 项</span>
    </div>
    <div class="selection-toolbar__actions">
      <ElButton @click="emit('toggle-select-page')">
        {{ 是否已全选当前页 ? '取消全选' : '全选' }}
      </ElButton>
      <ElButton @click="emit('clear-selection')">退出选择</ElButton>
      <ElButton :disabled="!当前选择可下载" @click="emit('download')">{{ 下载操作按钮文案 }}</ElButton>
      <ElButton :disabled="!当前选择可移动" @click="emit('open-move')">{{ 已选资源移动文案 }}</ElButton>
      <ElButton
        v-if="!是否全局搜索模式"
        :disabled="!当前选择可编辑"
        @click="emit('open-batch-rename')"
      >
        {{ 已选资源重命名文案 }}
      </ElButton>
      <ElButton type="danger" :disabled="!当前选择可编辑" @click="emit('delete')">{{ 已选资源删除文案 }}</ElButton>
    </div>
  </div>
</template>

<style scoped>
.selection-toolbar {
  position: fixed;
  left: 50%;
  bottom: calc(24px + var(--app-safe-area-bottom));
  transform: translateX(-50%);
  z-index: 1200;
  width: min(960px, calc(100vw - 48px));
  padding: 14px 16px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.22);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(18px);
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.16);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.selection-toolbar__summary {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  color: var(--el-text-color-primary);
  font-size: 14px;
  font-weight: 600;
}

.selection-toolbar__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

:global(.dark) .selection-toolbar {
  background: rgba(24, 24, 28, 0.92);
  border-color: rgb(var(--el-color-primary-rgb) / 0.32);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.36);
}

:global(.dark) .selection-toolbar__summary {
  color: #fff;
}

@media (max-width: 768px) {
  .selection-toolbar {
    width: calc(100vw - 20px);
    bottom: calc(12px + var(--app-safe-area-bottom));
    padding: 12px;
    border-radius: 14px;
    flex-direction: column;
    align-items: stretch;
  }

  .selection-toolbar__actions {
    justify-content: stretch;
  }

  .selection-toolbar__actions :deep(.el-button) {
    flex: 1 1 calc(50% - 4px);
    min-width: 0;
    margin-left: 0;
  }
}
</style>
