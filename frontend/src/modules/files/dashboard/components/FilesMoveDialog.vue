<script setup lang="ts">
import { ElButton, ElIcon, ElTree } from 'element-plus'
import { Folder, FolderOpened } from '@element-plus/icons-vue'
import BaseDialog from '../../../../components/BaseDialog.vue'
import type { 目录树节点 } from '../../core/shared'

defineProps<{
  visible: boolean
  待移动资源数量: number
  目录树数据: 目录树节点[]
  移动目标目录Id: string | null
  根目录名称: string
  根目录节点键: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'update:target-folder-id': [folderId: string | null]
  confirm: []
}>()
</script>

<template>
  <BaseDialog
    :model-value="visible"
    title="移动资源"
    width="420px"
    @update:model-value="emit('update:visible', $event)"
  >
    <div class="move-dialog__summary">
      即将移动 {{ 待移动资源数量 }} 项资源，选择下方目标目录即可。
    </div>

    <div class="move-dialog__picker">
      <button
        type="button"
        class="move-dialog__root"
        :class="{ 'is-active': 移动目标目录Id === null }"
        @click="emit('update:target-folder-id', null)"
      >
        <ElIcon><FolderOpened /></ElIcon>
        <span>{{ 根目录名称 }}</span>
      </button>

      <ElTree
        :data="目录树数据"
        node-key="id"
        default-expand-all
        :current-node-key="移动目标目录Id ?? 根目录节点键"
        :expand-on-click-node="false"
        empty-text="暂无文件夹"
        @node-click="(data: 目录树节点) => emit('update:target-folder-id', data.isRoot ? null : data.id)"
      >
        <template #default="{ data }">
          <div class="tree-node">
            <ElIcon class="tree-node__icon">
              <component :is="data.isRoot || data.id === 移动目标目录Id ? FolderOpened : Folder" />
            </ElIcon>
            <span class="tree-node__label">{{ data.name }}</span>
          </div>
        </template>
      </ElTree>
    </div>

    <template #footer>
      <ElButton @click="emit('update:visible', false)">取消</ElButton>
      <ElButton type="primary" @click="emit('confirm')">确认移动</ElButton>
    </template>
  </BaseDialog>
</template>

<style scoped>
.move-dialog__summary {
  margin-bottom: 14px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.move-dialog__picker {
  border: 1px solid var(--el-border-color);
  border-radius: 16px;
  padding: 12px;
  max-height: 360px;
  overflow: auto;
}

.move-dialog__root {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  margin-bottom: 10px;
  padding: 10px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  background: var(--el-fill-color-blank);
  cursor: pointer;
}

.move-dialog__root.is-active {
  border-color: rgb(var(--el-color-primary-rgb) / 0.45);
  background: rgb(var(--el-color-primary-rgb) / 0.08);
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
  padding: 4px 0;
}

.tree-node__icon {
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.tree-node__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
