<script setup lang="ts">
import {
  ElButton,
  ElIcon,
  ElInput,
  ElOption,
  ElSelect,
} from 'element-plus'
import { FolderOpened, Search, UploadFilled } from '@element-plus/icons-vue'

defineProps<{
  正在上传: boolean
  搜索关键词: string
  搜索框占位文案: string
  搜索范围值: string
  当前排序: string
  搜索范围选项: readonly { label: string; value: string }[]
  排序选项: readonly { label: string; value: string }[]
  是否禁用排序: boolean
}>()

const emit = defineEmits<{
  'update:search-keyword': [value: string]
  'update:search-scope': [value: string]
  'update:sort-value': [value: string]
  'upload-files': []
  'upload-folders': []
}>()
</script>

<template>
  <div class="page-header">
    <div class="page-heading">
      <h2 class="page-title">
        <ElIcon><FolderOpened /></ElIcon>
        <span>资源管理器</span>
      </h2>
    </div>
    <div class="page-actions">
      <ElButton :loading="正在上传" @click="emit('upload-folders')">
        <ElIcon class="page-action-icon"><FolderOpened /></ElIcon>
        <span>上传目录</span>
      </ElButton>
      <ElButton type="primary" :loading="正在上传" @click="emit('upload-files')">
        <ElIcon class="page-action-icon"><UploadFilled /></ElIcon>
        <span>上传文件</span>
      </ElButton>
    </div>
  </div>

  <div class="filter-toolbar page-filter-toolbar">
    <ElInput
      :model-value="搜索关键词"
      clearable
      :placeholder="搜索框占位文案"
      class="filter-toolbar__search"
      @update:model-value="emit('update:search-keyword', String($event ?? ''))"
    >
      <template #prefix>
        <ElIcon><Search /></ElIcon>
      </template>
    </ElInput>
    <ElSelect
      :model-value="搜索范围值"
      class="filter-toolbar__scope"
      @update:model-value="emit('update:search-scope', String($event))"
    >
      <ElOption
        v-for="option in 搜索范围选项"
        :key="option.value"
        :label="option.label"
        :value="option.value"
      />
    </ElSelect>
    <ElSelect
      :model-value="当前排序"
      class="filter-toolbar__sort"
      :disabled="是否禁用排序"
      @update:model-value="emit('update:sort-value', String($event))"
    >
      <ElOption
        v-for="option in 排序选项"
        :key="option.value"
        :label="option.label"
        :value="option.value"
      />
    </ElSelect>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
  flex-shrink: 0;
}

.page-heading {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.page-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.page-action-icon {
  width: 16px;
  height: 16px;
  margin-right: 6px;
  flex-shrink: 0;
}

.filter-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.page-filter-toolbar {
  margin-top: 0;
  margin-bottom: 14px;
  flex-shrink: 0;
}

.filter-toolbar__search {
  flex: 1;
  min-width: 220px;
}

.filter-toolbar__scope {
  width: 140px;
}

.filter-toolbar__sort {
  width: 180px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .page-actions {
    justify-content: flex-start;
  }

  .page-filter-toolbar {
    margin-bottom: 12px;
  }
}
</style>
